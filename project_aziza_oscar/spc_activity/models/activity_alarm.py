# -*- coding: utf-8 -*-
import logging

from odoo import api ,models, fields, _
from datetime import datetime, timedelta, MAXYEAR
_logger = logging.getLogger(__name__)



class AlarmManager(models.AbstractModel):
    _name = 'activity.alarm_manager'
    _description = 'Activity Alarm Manager'

    def get_next_potential_limit_alarm(self, alarm_type, seconds=None, partner_id=None):
        result = {}
        delta_request = """
            SELECT
                 rel.mail_activity_id, max(alarm.duration_minutes) AS max_delta,min(alarm.duration_minutes) AS min_delta
            FROM
                activity_alarm_mail_activity_rel AS rel
            LEFT JOIN activity_alarm AS alarm ON alarm.id = rel.activity_alarm_id
            WHERE alarm.type = %s
            GROUP BY rel.mail_activity_id

        """
        base_request = """
                    SELECT
                        cal.id,
                        cal.start - interval '1' minute  * calcul_delta.max_delta AS first_alarm,
                        CASE
                            WHEN cal.reccurrent THEN cal.final_date - interval '1' minute  * calcul_delta.min_delta
                            ELSE cal.stop - interval '1' minute  * calcul_delta.min_delta
                        END as last_alarm,
                        cal.start as first_event_date,
                        CASE
                            WHEN cal.reccurrent THEN cal.final_date
                            ELSE cal.stop
                        END as last_event_date,
                        calcul_delta.min_delta,
                        calcul_delta.max_delta,
                        cal.rrule AS rule
                    FROM
                        mail_activity AS cal
                    RIGHT JOIN calcul_delta ON calcul_delta.mail_activity_id = cal.id
             """

        filter_user = """
                RIGHT JOIN mail_activity AS part_rel ON part_rel.id = cal.id
                    AND part_rel.user_id = %s
        """

        # Add filter on alarm type
        tuple_params = (alarm_type,)

        # Add filter on partner_id
        if partner_id:
            base_request += filter_user
            tuple_params += (partner_id,)

        # Upper bound on first_alarm of requested events
        first_alarm_max_value = ""
        if seconds is None:
            # first alarm in the future + 3 minutes if there is one, now otherwise
            first_alarm_max_value = """
                COALESCE((SELECT MIN(cal.start - interval '1' minute  * calcul_delta.max_delta)
                FROM mail_activity cal
                RIGHT JOIN calcul_delta ON calcul_delta.mail_activity_id = cal.id
                WHERE cal.start - interval '1' minute  * calcul_delta.max_delta > now() at time zone 'utc'
            ) + interval '3' minute, now() at time zone 'utc')"""
        else:
            # now + given seconds
            first_alarm_max_value = "(now() at time zone 'utc' + interval '%s' second )"
            tuple_params += (seconds,)

        self._cr.execute("""
                    WITH calcul_delta AS (%s)
                    SELECT *
                        FROM ( %s WHERE cal.active = True ) AS ALL_EVENTS
                       WHERE ALL_EVENTS.first_alarm < %s
                         AND ALL_EVENTS.last_event_date > (now() at time zone 'utc')
                   """ % (delta_request, base_request, first_alarm_max_value), tuple_params)

        for activity_id, first_alarm, last_alarm, first_meeting, last_meeting, min_duration, max_duration, rule in self._cr.fetchall():
            result[activity_id] = {
                'activity_id': activity_id,
                'first_alarm': first_alarm,
                'last_alarm': last_alarm,
                'first_meeting': first_meeting,
                'last_meeting': last_meeting,
                'min_duration': min_duration,
                'max_duration': max_duration,
                'rrule': rule
            }

        # determine accessible events
        events = self.env['mail.activity'].browse(result)
        result = {
            key: result[key]
            for key in set(events._filter_access_rules('read').ids)
        }
        return result

    def do_check_alarm_for_one_date(self, one_date, event, event_maxdelta, in_the_next_X_seconds, alarm_type,
                                    after=False, missing=False):
        """ Search for some alarms in the interval of time determined by some parameters (after, in_the_next_X_seconds, ...)
            :param one_date: date of the event to check (not the same that in the event browse if recurrent)
            :param event: Event browse record
            :param event_maxdelta: biggest duration from alarms for this event
            :param in_the_next_X_seconds: looking in the future (in seconds)
            :param after: if not False: will return alert if after this date (date as string - todo: change in master)
            :param missing: if not False: will return alert even if we are too late
            :param notif: Looking for type notification
            :param mail: looking for type email
        """
        result = []
        # TODO: remove event_maxdelta and if using it
        if one_date - timedelta(minutes=(missing and 0 or event_maxdelta)) < datetime.now() + timedelta(
                seconds=in_the_next_X_seconds):  # if an alarm is possible for this date
            for alarm in event.alarm_ids:
                if alarm.type == alarm_type and \
                        one_date - timedelta(
                    minutes=(missing and 0 or alarm.duration_minutes)) < datetime.now() + timedelta(
                    seconds=in_the_next_X_seconds) and \
                        (not after or one_date - timedelta(
                            minutes=alarm.duration_minutes) > fields.Datetime.from_string(after)):
                    alert = {
                        'alarm_id': alarm.id,
                        'activity_id': event.id,
                        'notify_at': one_date - timedelta(minutes=alarm.duration_minutes),
                    }
                    result.append(alert)
        return result

    @api.model
    def get_next_mail_activity(self):
        now = fields.Datetime.to_string(fields.Datetime.now())
        last_notif_mail = self.env['ir.config_parameter'].sudo().get_param('spc_activity.last_notif_mail', default=now)

        try:
            cron = self.env['ir.model.data'].sudo().get_object('spc_activity', 'ir_cron_scheduler_alarm_for_activity')
        except ValueError:
            _logger.error("Cron for " + self._name + " can not be identified !")
            return False

        interval_to_second = {
            "weeks": 7 * 24 * 60 * 60,
            "days": 24 * 60 * 60,
            "hours": 60 * 60,
            "minutes": 60,
            "seconds": 1
        }

        if cron.interval_type not in interval_to_second:
            _logger.error("Cron delay can not be computed !")
            return False

        cron_interval = cron.interval_number * interval_to_second[cron.interval_type]

        all_meetings = self.get_next_potential_limit_alarm('email', seconds=cron_interval)

        for meeting in self.env['mail.activity'].browse(all_meetings):
            max_delta = all_meetings[meeting.id]['max_duration']

            if meeting.reccurrent:
                at_least_one = False
                last_found = False
                for one_date in meeting._get_recurrent_date_by_event():
                    in_date_format = one_date.replace(tzinfo=None)
                    last_found = self.do_check_alarm_for_one_date(in_date_format, meeting, max_delta, 0, 'email',
                                                                  after=last_notif_mail, missing=True)
                    for alert in last_found:
                        self.do_mail_reminder(alert)
                        at_least_one = True  # if it's the first alarm for this recurrent event
                    if at_least_one and not last_found:  # if the precedent event had an alarm but not this one, we can stop the search for this event
                        break
            else:
                in_date_format = meeting.start
                last_found = self.do_check_alarm_for_one_date(in_date_format, meeting, max_delta, 0, 'email', after=last_notif_mail, missing=True)
                for alert in last_found:
                    self.do_mail_reminder(alert)
        self.env['ir.config_parameter'].sudo().set_param('spc_activity.last_notif_mail', now)

    def do_mail_reminder(self, alert):
        meeting = self.env['mail.activity'].browse(alert['activity_id'])
        alarm = self.env['activity.alarm'].browse(alert['alarm_id'])

        result = False
        if alarm.type == 'email':
            result = meeting.attendee_ids._send_mail_to_attendees('spc_activity.spc_calendar_template_meeting_reminder_by_mail', force_send=True)
        return result


    @api.model
    def get_next_notif(self):
        partner = self.env.user
        all_notif = []

        if not partner:
            return []

        all_meetings = self.get_next_potential_limit_alarm('notification', partner_id=partner.id)
        time_limit = 3600 * 24  # return alarms of the next 24 hours
        for activity_id in all_meetings:
            max_delta = all_meetings[activity_id]['max_duration']
            meeting = self.env['mail.activity'].browse(activity_id)
            if meeting.reccurrent:
                b_found = False
                last_found = False
                for one_date in meeting._get_recurrent_date_by_event():
                    in_date_format = one_date.replace(tzinfo=None)
                    last_found = self.do_check_alarm_for_one_date(in_date_format, meeting, max_delta, time_limit,
                                                                  'notification', after=partner.activity_last_notif_ack)
                    if last_found:
                        for alert in last_found:
                            all_notif.append(self.do_notif_reminder(alert))
                        if not b_found:  # if it's the first alarm for this recurrent event
                            b_found = True
                    if b_found and not last_found:  # if the precedent event had alarm but not this one, we can stop the search fot this event
                        break
            else:
                in_date_format = fields.Datetime.from_string(meeting.start)
                last_found = self.do_check_alarm_for_one_date(in_date_format, meeting, max_delta, time_limit,
                                                              'notification', after=partner.activity_last_notif_ack)
                if last_found:
                    for alert in last_found:
                        all_notif.append(self.do_notif_reminder(alert))
        return all_notif

    def do_notif_reminder(self, alert):
        alarm = self.env['activity.alarm'].browse(alert['alarm_id'])
        meeting = self.env['mail.activity'].browse(alert['activity_id'])

        if alarm.type == 'notification':
            message = meeting.display_time

            delta = alert['notify_at'] - datetime.now()
            delta = delta.seconds + delta.days * 3600 * 24

            return {
                'activity_id': meeting.id,
                'title': meeting.summary,
                'message': message,
                'timer': delta,
                'notify_at': fields.Datetime.to_string(alert['notify_at']),
            }

    def notify_next_alarm(self, partner_ids):
        """ Sends through the bus the next alarm of given partners """
        notifications = []
        users = self.env['res.users'].search([('partner_id', 'in', tuple(partner_ids))])
        for user in users:
            notif = self.sudo(user.id).get_next_notif()
            notifications.append([(self._cr.dbname, 'activity.alarm', user.partner_id.id), notif])
        if len(notifications) > 0:
            self.env['bus.bus'].sendmany(notifications)


class Alarm(models.Model):
    _name = 'activity.alarm'
    _description = 'Activity Alarm'

    @api.depends('interval', 'duration')
    def _compute_duration_minutes(self):
        for alarm in self:
            if alarm.interval == "minutes":
                alarm.duration_minutes = alarm.duration
            elif alarm.interval == "hours":
                alarm.duration_minutes = alarm.duration * 60
            elif alarm.interval == "days":
                alarm.duration_minutes = alarm.duration * 60 * 24
            else:
                alarm.duration_minutes = 0

    _interval_selection = {'minutes': 'Minute(s)', 'hours': 'Hour(s)', 'days': 'Day(s)'}

    name = fields.Char('Name', translate=True, required=True)
    type = fields.Selection([('notification', 'Notification'), ('email', 'Email')], 'Type', required=True,
                            default='email')
    duration = fields.Integer('Remind Before', required=True, default=1)
    interval = fields.Selection(list(_interval_selection.items()), 'Unit', required=True, default='hours')
    duration_minutes = fields.Integer('Duration in minutes', compute='_compute_duration_minutes', store=True,
                                      help="Duration in minutes")

    @api.onchange('duration', 'interval')
    def _onchange_duration_interval(self):
        display_interval = self._interval_selection.get(self.interval, '')
        self.name = str(self.duration) + ' ' + display_interval

    def _update_cron(self):
        try:
            cron = self.env['ir.model.data'].sudo().get_object('spc_activity', 'ir_cron_scheduler_alarm_for_activity')
        except ValueError:
            return False
        return cron.toggle(model=self._name, domain=[('type', '=', 'email')])

    @api.model
    def create(self, values):
        result = super(Alarm, self).create(values)
        self._update_cron()
        return result

    @api.multi
    def write(self, values):
        result = super(Alarm, self).write(values)
        self._update_cron()
        return result

    @api.multi
    def unlink(self):
        result = super(Alarm, self).unlink()
        self._update_cron()
        return result
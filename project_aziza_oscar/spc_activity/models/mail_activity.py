# -*- coding: utf-8 -*-
import logging
import datetime
from datetime import timedelta
import pytz
import babel.dates
import uuid
import base64
import sys


from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
from odoo import tools
from dateutil.relativedelta import relativedelta
from calendar import monthrange


from odoo import api ,models, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Attendee(models.Model):
    """ Calendar Attendee Information """

    _name = 'activity.attendee'
    _rec_name = 'common_name'
    _description = 'Activity Attendee Information'

    def _default_access_token(self):
        return uuid.uuid4().hex

    STATE_SELECTION = [
        ('needsAction', 'Needs Action'),
        ('tentative', 'Uncertain'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted'),
    ]

    common_name = fields.Char('Common name', compute='_compute_common_name', store=True)
    state = fields.Selection(STATE_SELECTION, string='Status', readonly=True, default='needsAction',
                             help="Status of the attendee's participation")
    partner_id = fields.Many2one('res.partner', 'Contact', readonly="True")
    email = fields.Char('Email', help="Email of Invited Person")
    access_token = fields.Char('Invitation Token', default=_default_access_token)
    activity_id = fields.Many2one('mail.activity', 'Activities linked')
    workflow_activity = fields.Selection(related="activity_id.workflow_activity", store=True)

    @api.depends('partner_id', 'partner_id.name', 'email')
    def _compute_common_name(self):
        for attendee in self:
            attendee.common_name = attendee.partner_id.name or attendee.email

    # This is for verification
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Make entry on email and availability on change of partner_id field. """
        self.email = self.partner_id.email

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get("email") and values.get("common_name"):
                common_nameval = values.get("common_name").split(':')
                email = [x for x in common_nameval if '@' in x]  # TODO JEM : should be refactored
                values['email'] = email and email[0] or ''
                values['common_name'] = values.get("common_name")
        return super(Attendee, self).create(vals_list)

    @api.multi
    def do_tentative(self):
        """ Makes event invitation as Tentative. """
        if any(workflow_activity in ('done', 'validated') for workflow_activity in set(self.mapped('workflow_activity'))):
            raise UserError(_("Aucune modification à l'état terminé ou validé"))
        else:
            return self.write({'state': 'tentative'})

    @api.multi
    def do_accept(self):
        """ Marks event invitation as Accepted. """
        if any(workflow_activity in ('done', 'validated') for workflow_activity in set(self.mapped('workflow_activity'))):
            raise UserError(_("Aucune modification à l'état terminé ou validé"))
        else:
            result = self.write({'state': 'accepted'})
            for attendee in self:
                attendee.activity_id.message_post(body=_("%s has accepted invitation") % (attendee.common_name),
                                               subtype="spc_activity.subtype_invitation")
            return result

    @api.multi
    def do_decline(self):
        """ Marks event invitation as Declined. """
        if any(workflow_activity in ('done', 'validated') for workflow_activity in set(self.mapped('workflow_activity'))):
            raise UserError(_("Aucune modification à l'état terminé ou validé"))
        else:
            res = self.write({'state': 'declined'})
            for attendee in self:
                attendee.activity_id.message_post(body=_("%s has declined invitation") % (attendee.common_name),
                                               subtype="spc_activity.subtype_invitation")
            return res

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        """ Send mail for event invitation to event attendees.
            :param template_xmlid: xml id of the email template to use to send the invitation
            :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
        """
        res = False

        if self.env['ir.config_parameter'].sudo().get_param('spc_activity.block_mail') or self._context.get("no_mail_to_attendees"):
            return res

        calendar_view = self.env.ref('spc_activity.spc_mail_activity_view_calendar_inherit')
        invitation_template = self.env.ref(template_xmlid)

        # get ics file for all meetings
        ics_files = self.mapped('activity_id')._get_ics_file()

        # prepare rendering context for mail template
        colors = {
            'needsAction': 'grey',
            'accepted': 'green',
            'tentative': '#FFFF00',
            'declined': 'red'
        }
        rendering_context = dict(self._context)
        rendering_context.update({
            'color': colors,
            'action_id': self.env['ir.actions.act_window'].search([('view_id', '=', calendar_view.id)], limit=1).id,
            # 'action_id': 424,
            'dbname': self._cr.dbname,
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url',
                                                                         default='http://localhost:8069')
        })
        invitation_template = invitation_template.with_context(rendering_context)

        # send email with attachments
        mails_to_send = self.env['mail.mail']
        for attendee in self:
            if attendee.email or attendee.partner_id.email:
                # FIXME: is ics_file text or bytes?
                ics_file = ics_files.get(attendee.activity_id.id)
                mail_id = invitation_template.send_mail(attendee.id, notif_layout='mail.mail_notification_light')

                vals = {}
                if ics_file:
                    vals['attachment_ids'] = [(0, 0, {'name': 'invitation.ics',
                                                      'mimetype': 'text/calendar',
                                                      'datas_fname': 'invitation.ics',
                                                      'datas': base64.b64encode(ics_file)})]
                vals['model'] = None  # We don't want to have the mail in the tchatter while in queue!
                vals['res_id'] = False
                current_mail = self.env['mail.mail'].browse(mail_id)
                current_mail.mail_message_id.write(vals)
                mails_to_send |= current_mail

        if force_send and mails_to_send:
            res = mails_to_send.send()

        return res


class MailActivity(models.Model):
    _name = 'mail.activity'
    _description = 'Activity'
    _inherit = ["mail.activity", "mail.thread"]

    # region Default methods
    @api.model
    def default_get(self, fields):
        res = super(MailActivity, self).default_get(fields)
        if not fields or 'res_model_id' in fields:
            model_id = self.env['ir.model'].search([('model', '=', 'mail.activity')]).id
            res_id = self.search([('code', 'like', '10'), ('active', '=', False)])
            res['res_model_id'] = model_id
            res['res_id'] = res_id.id
        return res

    @api.model
    def _default_partners(self):
        """ When active_model is res.partner, the current partners should be attendees """
        partners = self.env.user.partner_id
        active_id = self._context.get('active_id')
        if self._context.get('active_model') == 'res.partner' and active_id:
            if active_id not in partners.ids:
                partners |= self.env['res.partner'].browse(active_id)
        return partners

    @api.multi
    def _find_my_attendee(self):
        """ Return the first attendee where the user connected has been invited
            from all the meeting_ids in parameters.
        """
        self.ensure_one()
        for attendee in self.attendee_ids:
            if self.env.user.partner_id == attendee.partner_id:
                return attendee
        return False

    @api.model
    def _get_date_formats(self):
        """ get current date and time format, according to the context lang
            :return: a tuple with (format date, format time)
        """
        lang = self._context.get("lang")
        lang_params = {}
        if lang:
            record_lang = self.env['res.lang'].with_context(active_test=False).search([("code", "=", lang)], limit=1)
            lang_params = {
                'date_format': record_lang.date_format,
                'time_format': record_lang.time_format
            }

        # formats will be used for str{f,p}time() which do not support unicode in Python 2, coerce to str
        format_date = pycompat.to_native(lang_params.get("date_format") or '%B-%d-%Y')
        format_time = pycompat.to_native(lang_params.get("time_format") or '%I-%M %p')
        return (format_date, format_time)

    @api.model
    def _get_recurrent_fields(self):
        return ['byday', 'reccurrent', 'final_date', 'rrule_type', 'month_by',
                'interval', 'count', 'end_type', 'mo', 'tu', 'we', 'th', 'fr', 'sa',
                'su', 'day', 'week_list']

    @api.model
    def _get_display_time(self, start, stop, zduration, zallday):
        """ Return date and time (from to from) based on duration with timezone in string. Eg :
                1) if user add duration for 2 hours, return : August-23-2013 at (04-30 To 06-30) (Europe/Brussels)
                2) if event all day ,return : AllDay, July-31-2013
        """
        timezone = self._context.get('tz') or self.env.user.partner_id.tz or 'UTC'
        timezone = pycompat.to_native(timezone)  # make safe for str{p,f}time()

        # get date/time format according to context
        format_date, format_time = self._get_date_formats()

        # convert date and time into user timezone
        self_tz = self.with_context(tz=timezone)
        if start and stop:
            date = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(start))
            date_limite = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(stop))

            # convert into string the date and time, using user formats
            to_text = pycompat.to_text
            date_str = to_text(date.strftime(format_date))
            time_str = to_text(date.strftime(format_time))

            if zallday:
                display_time = _("AllDay , %s") % (date_str)
            elif zduration < 24:
                duration = date + timedelta(hours=zduration)
                duration_time = to_text(duration.strftime(format_time))
                display_time = _(u"%s at (%s To %s) (%s)") % (
                    date_str,
                    time_str,
                    duration_time,
                    timezone,
                )
            else:
                dd_date = to_text(date_limite.strftime(format_date))
                dd_time = to_text(date_limite.strftime(format_time))
                display_time = _(u"%s at %s To\n %s at %s (%s)") % (
                    date_str,
                    time_str,
                    dd_date,
                    dd_time,
                    timezone,
                )
            return display_time

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
                return round(duration, 2)
            return 0.0
    # endregion

    # region Fields Declaration
    activity_type_id = fields.Many2one('mail.activity.type', 'Activity')
    summary = fields.Char('Summary', required=True)
    res_id = fields.Integer('Related Document ID', index=True, required=False)
    res_model_id = fields.Many2one(
        'ir.model', 'Document Model',
        index=True, required=False)
    is_attendee = fields.Boolean('Attendee', compute='_compute_attendee')
    attendee_status = fields.Selection(Attendee.STATE_SELECTION, string='Attendee Status', compute='_compute_attendee')
    display_time = fields.Char('Event Time', compute='_compute_display_time')
    display_start = fields.Char('Date', compute='_compute_display_start', store=True)
    code = fields.Char(string='Code', index=True)
    active = fields.Boolean(string='Activé', default=True)
    start = fields.Datetime('Start', help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop', help="Stop date of an event, without time for full days events")
    allday = fields.Boolean('Toute la journée',  default=False)
    start_date = fields.Date('Start Date', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    start_datetime = fields.Datetime('Start DateTime', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    stop_date = fields.Date('End Date', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')
    stop_datetime = fields.Datetime('End Datetime', compute='_compute_dates', inverse='_inverse_dates', store=True, track_visibility='onchange')  # old date_limite
    date_limite = fields.Date('Date écheance', index=True, required=True, default=fields.Date.context_today)

    duration = fields.Float('Duration')
    privacy = fields.Selection([('public', 'Public'), ('private', 'Moi seulement'), ('by_group', 'Par groupe')], 'Privacy', default='by_group', oldname="class")
    show_as = fields.Selection([('free', 'Free'), ('busy', 'Busy')], 'Show Time as', default='busy')
    group_ids = fields.Many2many('res.groups',
                                 string='Groupes',related='activity_type_id.group_ids',
                                 help="Ce champs est utilisé pour associé des groupes à une activité.")
    resource_ref = fields.Reference(string='Référence', selection='_selection_target_model')
    user_id = fields.Many2one('res.users', 'Utilisateur', default=lambda self: self.env.user, index=True, required=False)
    partner_id = fields.Many2one('res.partner', string='Responsable', related='user_id.partner_id', readonly=True)
    tag_ids = fields.Many2many('mail.activity.tags', 'activity_category_rel', 'activity_id', 'type_id', 'Étiquettes')
    alarm_ids = fields.Many2many('activity.alarm', 'activity_alarm_mail_activity_rel', string='Rappels', ondelete="restrict", copy=False)
    description = fields.Text('Description')
    location = fields.Char('Lieu', track_visibility='onchange', help="Location of Event")
    attendee_ids = fields.One2many('activity.attendee', 'activity_id', 'Participant')
    manager_ids = fields.One2many('manager.user', 'activity_id', 'Manager')
    partner_ids = fields.Many2many('res.partner', 'mail_activity_res_partner_rel', string='Participants', default=_default_partners)
    workflow_activity = fields.Selection([('new', 'Nouvelle'),
                                          ('validated', 'Validée'),
                                          ('canceled', 'Annulée'),
                                          ('done', 'Terminée'),
                                          ('untreated', 'Non traité'),], default='new', string="Statut", track_visibility='onchange')
    user_ids = fields.Many2many('res.users', 'res_users_mail_activity_rel', 'activity_id', 'user_id', string='Utilisateurs',
                                default=lambda self: self.env.user, help='Assigné à un ensemble des utilisateurs')
    group_id = fields.Many2one('res.groups', 'Groupe', index=True)
    by_mass = fields.Selection([('individual', 'Utilisateur(s)'), ('by_group', 'Groupe')],
                               string='Assigné à',
                               default='individual')
    by_pass = fields.Boolean(default=True)
    # act_model_id = fields.Many2one('ir.model', string="Objet", related='activity_type_id.model_id')
    # RECURRENCE FIELD
    activity_parent_id = fields.Many2one('mail.activity', string="Activité d'origine",
                                         help='Task from which this one originated', readonly=True)

    activity_child_ids = fields.One2many('mail.activity', 'activity_parent_id', 'Activités répétitives',
                                         help='Tasks originated from this one')
    activity_has_sisters = fields.Boolean('Has sisters?', compute='act_get_has_sisters')
    rrule = fields.Char('Recurrent Rule')
    rrule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')
    ], string='Recurrence',
        help="Let the event automatically repeat at that interval")
    reccurrent = fields.Boolean('Recurrent', help="Recurrent Meeting")
    end_type = fields.Selection([
        ('count', 'Number of repetitions'),
        ('end_date', 'End date')
    ], string='Recurrence Termination', default='count')
    interval = fields.Integer(string='Repeat Every', default=1, help="Repeat every (Days/Week/Month/Year)")
    count = fields.Integer(string='Repeat', help="Repeat x times", default=1)
    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')
    month_by = fields.Selection([
        ('date', 'Date of month'),
        ('day', 'Day of month')
    ], string='Option', default='date', oldname='select1')
    day = fields.Integer('Date of month', default=1)
    week_list = fields.Selection([
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ], string='Weekday')
    byday = fields.Selection([
        ('1', 'First'),
        ('2', 'Second'),
        ('3', 'Third'),
        ('4', 'Fourth'),
        ('5', 'Fifth'),
        ('-1', 'Last')
    ], string='By day')
    final_date = fields.Date('Repeat Until')
    change_date = fields.Selection([('next_day', 'Next available day'), ('previous_day', 'Previous available day')],
                                   'Change date (if it is invalid)', default='previous_day')
    # Nombre de rejet
    reset_ids = fields.One2many('spc.activity.reset', 'activity_id', string='Réinitialisations', readonly=True)
    count_reset = fields.Integer("Réinitialisation", compute="_compute_count_reset")
    # endregion

    # region Computed method
    def _compute_count_reset(self):
        reset_data = self.env['spc.activity.reset'].sudo().read_group([('activity_id', 'in', self.ids)],
                                                                      ['activity_id'], ['activity_id'])
        result = dict((data['activity_id'][0], data['activity_id_count']) for data in reset_data)
        for activity in self:
            activity.count_reset = result.get(activity.id, 0)

    @api.one
    @api.depends('activity_parent_id')
    def act_get_has_sisters(self):
        res = False
        if self.activity_parent_id:
            if self.search([('activity_parent_id', '=', self.activity_parent_id.id)], limit=1):
                res = True
        self.activity_has_sisters = res

    @api.onchange('privacy')
    def onchange_privacy(self):
        if self.privacy in ['public', 'private']:
            self.group_ids = False
        if self.privacy == 'by_group':
            self.group_ids = self.activity_type_id.group_ids

    @api.multi
    def _compute_attendee(self):
        for meeting in self:
            attendee = meeting._find_my_attendee()
            meeting.is_attendee = bool(attendee)
            meeting.attendee_status = attendee.state if attendee else 'needsAction'

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        if self.res_model and self.res_id:
            for activity in self:
                activity.res_name = self.env[activity.res_model].browse(activity.res_id).name_get()[0][1]


    @api.multi
    def _compute_display_time(self):
        for meeting in self:
            meeting.display_time = self._get_display_time(meeting.start, meeting.stop, meeting.duration, meeting.allday)

    @api.multi
    @api.depends('allday', 'start_date', 'start_datetime')
    def _compute_display_start(self):
        for meeting in self:
            meeting.display_start = meeting.start_date if meeting.allday else meeting.start_datetime

    @api.multi
    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        """ Adapt the value of start_date(time)/stop_date(time) according to start/stop fields and allday. Also, compute
            the duration for not allday meeting ; otherwise the duration is set to zero, since the meeting last all the day.
        """
        for activity in self:
            if activity.allday and activity.start and activity.stop:
                activity.start_date = activity.start.date()
                # activity.start_datetime = False
                activity.stop_date = activity.stop.date()
                activity.stop_datetime = False

                activity.duration = 0.0
            else:
                activity.start_date = False
                activity.start_datetime = activity.start
                activity.stop_date = False
                activity.stop_datetime = activity.stop

                activity.duration = self._get_duration(activity.start, activity.stop)

    @api.multi
    def _inverse_dates(self):
        for activity in self:
            if activity.allday:

                # Convention break:
                # stop and start are NOT in UTC in allday event
                # in this case, they actually represent a date
                # i.e. Christmas is on 25/12 for everyone
                # even if people don't celebrate it simultaneously
                enddate = fields.Datetime.from_string(activity.stop_date)
                enddate = enddate.replace(hour=18)

                startdate = fields.Datetime.from_string(activity.start_date)
                startdate = startdate.replace(hour=8)  # Set 8 AM

                activity.write({
                    'start': startdate.replace(tzinfo=None),
                    'stop': enddate.replace(tzinfo=None)
                })
            else:
                activity.write({'start': activity.start_datetime,
                                'stop': activity.stop_datetime})

    # endregion

    # region Constraints and Onchange

    # @api.constrains('user_id', 'start_datetime', 'stop_datetime')
    # def _check_same_user(self):
    #     for activity in self:
    #         domain = [
    #             ('start_datetime', '<', activity.stop_datetime),
    #             ('stop_datetime', '>', activity.start_datetime),
    #             ('user_id', '=', activity.user_id.id),
    #             ('id', '!=', activity.id),
    #         ]
    #         nbr_activity = self.search_count(domain)
    #         if nbr_activity:
    #             raise ValidationError(_('Vous ne pouvez pas avoir deux activités au même temps pour le même responsable!'))

    # This is for verification
    @api.onchange('activity_type_id')
    def onchange_activity(self):
        if self.activity_type_id.model_id:
            model_conf = self.env['mail.activity.type'].search(
                [('model_id', '=', self.activity_type_id.model_id.id)], order='id desc', limit=1)
            for rec in self:
                model_name = model_conf.model_id.model
                if model_conf.model_id:
                    rec.resource_ref = '%s,%s' % (model_name, model_conf.id)
        elif self.activity_type_id.resource_ref:
            for rec in self:
                    rec.resource_ref = self.activity_type_id.resource_ref
        else:
            self.resource_ref = False


    @api.constrains('start_datetime', 'stop_datetime', 'start_date', 'stop_date')
    def _check_closing_date(self):
        for meeting in self:
            if meeting.start_datetime and meeting.stop_datetime and meeting.stop_datetime < meeting.start_datetime:
                raise ValidationError(
                    _('The ending date and time cannot be earlier than the starting date and time.') + '\n' +
                    _("Meeting '%s' starts '%s' and ends '%s'") % (
                    meeting.summary, meeting.start_datetime, meeting.stop_datetime)
                )
            if meeting.start_date and meeting.stop_date and meeting.stop_date < meeting.start_date:
                raise ValidationError(
                    _('The ending date cannot be earlier than the starting date.') + '\n' +
                    _("Meeting '%s' starts '%s' and ends '%s'") % (meeting.summary, meeting.start_date, meeting.stop_date)
                )

    @api.onchange('user_ids')
    def onchange_user(self):
        if self.user_ids:
            self.user_id = self.user_ids[0]

    @api.onchange('start_datetime', 'duration')
    def _onchange_duration(self):
        if self.start_datetime:
            start = self.start_datetime
            self.start = self.start_datetime
            self.stop = start + timedelta(hours=self.duration) - timedelta(seconds=1)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            self.start = datetime.datetime.combine(self.start_date, datetime.time.min)

    @api.onchange('stop_date')
    def _onchange_stop_date(self):
        if self.stop_date:
            self.stop = datetime.datetime.combine(self.stop_date, datetime.time.max)

    # This is for verification
    @api.onchange('resource_ref')
    def onchange_resource_ref(self):
        if self.resource_ref:
            model_name = self.resource_ref._name
            active_id = self.env['ir.model'].search([('model', '=', model_name)]).id
            self.res_id = self.resource_ref
            self.res_model_id = active_id

    @api.onchange('activity_type_id', 'start_datetime')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            # Date.context_today is correct because date_limite is a Date and is meant to be
            # expressed in user TZ
            base = fields.Date.context_today(self)
            if self.activity_type_id.delay_from == 'previous_activity' and 'activity_previous_deadline' in self.env.context:
                base = fields.Date.from_string(self.env.context.get('activity_previous_deadline'))
            if self.start_datetime:
                start_datetime = str(self.start_datetime)
                base = datetime.datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S").date()
            if self.env.context.get('default_start'):
                default_start = self.env.context.get('default_start')
                base = datetime.datetime.strptime(default_start, "%Y-%m-%d %H:%M:%S").date()
            self.date_limite = base

    # endregion
    ####################################################
    # Reccurency Activity from create
    ####################################################
    @api.multi
    def create_task(self, deadline, start_datetime, stop_datetime):

        new_id = False
        if deadline:
            # we create a copy of the activity but with the new deadline
            vals = {
                'date_limite': deadline,
                'activity_parent_id': self.id,
                'start_datetime': start_datetime,
                'stop_datetime': stop_datetime,
                'reccurrent': False,
                # 'date_start': deadline,
            }
            try:
                new_id = self.env['mail.activity'].browse(self.id).copy(default=vals)
            except:
                _logger.error(str(sys.exc_info()[0]))
        return new_id

    def calculate_date(self, date=False, unit=False, amount=0):
        res_date = False

        if date and unit:
            res_date = date

            if unit == 'daily':
                res_date += relativedelta(days=amount)
            elif unit == 'weekly':
                res_date += relativedelta(weeks=amount)
            elif unit == 'monthly':
                res_date += relativedelta(months=amount)
            elif unit == 'yearly':
                res_date += relativedelta(years=amount)

        return res_date

        # If final_date is required but no value was received, let's make some calculations

    def get_default_final_date(self, unit, interval, count):

        res_date = datetime.date.today()

        units_to_add = interval * count

        if unit == 'daily':
            res_date += relativedelta(days=units_to_add)
        elif unit == 'weekly':
            res_date += relativedelta(weeks=units_to_add)
        elif unit == 'monthly':
            res_date += relativedelta(months=units_to_add)
        elif unit == 'yearly':
            res_date += relativedelta(years=units_to_add)

        # so that we don't get stuck in a comparison
        res_date += relativedelta(days=1)
        res_date = datetime.datetime.strptime(str(res_date), "%Y-%m-%d")

        return res_date

    @api.one
    def create_repetition(self):

        # date of the original task deadline
        deadline = self.start
        start = self.start
        stop = self.stop
        if deadline:
            deadline = deadline
        else:
            deadline = datetime.datetime.now()

        # deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
        final_date = self.final_date and datetime.datetime.strptime(str(self.final_date), "%Y-%m-%d")

        days_by_month = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
        days = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
        if self.rrule_type == 'weekly':
            days_chosen = False
            for d in days:
                if eval('self.' + d):
                    days_chosen = True
                    break
        else:
            days_chosen = False

        # We take the initial date and for COUNT times we add INTERVAL RRULE_TYPE
        for x in range(0, self.count):

            date_ok = True

            if (
                    self.rrule_type in ['daily', 'yearly']
                    or (self.rrule_type == 'weekly' and not days_chosen)
                    or (self.rrule_type == 'monthly' and not self.month_by)
            ):

                if self.end_type == 'count':
                    deadline = self.calculate_date(deadline, self.rrule_type, self.interval)
                    start = self.calculate_date(start, self.rrule_type, self.interval)
                    stop = self.calculate_date(stop, self.rrule_type, self.interval)
                    self.create_task(deadline, start, stop)
                else:
                    while date_ok:
                        deadline = self.calculate_date(deadline, self.rrule_type, self.interval)
                        start = self.calculate_date(start, self.rrule_type, self.interval)
                        stop = self.calculate_date(stop, self.rrule_type, self.interval)
                        deadline_weekly = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
                        if deadline_weekly <= final_date:
                            self.create_task(deadline, start, stop)
                        else:
                            date_ok = False


            elif (self.rrule_type == 'monthly' and self.month_by):

                # Every INTERVAL months, on day DAY, we create a task
                if self.month_by == 'date':
                    """
                    In this case, we don't start calculations by adding months to the original deadline.
                    We just go to the "next" month and, there, create the task on the chosen day.
                    """
                    date_ok = True
                    if not final_date:
                        final_date = self.get_default_final_date(self.rrule_type, self.interval, self.count)

                    while date_ok:
                        deadline = self.calculate_date(deadline, self.rrule_type, self.interval)
                        start = self.calculate_date(start, self.rrule_type, self.interval)
                        stop = self.calculate_date(stop, self.rrule_type, self.interval)
                        if deadline <= final_date:

                            this_date_ok = False
                            aux_date = deadline
                            aux_start = start
                            aux_stop = stop
                            chosen_day = self.day

                            while not this_date_ok:
                                try:
                                    aux_date = aux_date.replace(day=chosen_day)
                                    aux_start = aux_start.replace(day=chosen_day)
                                    aux_stop = aux_stop.replace(day=chosen_day)
                                    this_date_ok = True
                                except:
                                    if self.change_date == 'previous_day':
                                        chosen_day -= 1
                                    else:
                                        if chosen_day < 31:
                                            chosen_day += 1
                                        else:
                                            chosen_day = 1
                                            aux_date = deadline + relativedelta(months=1)
                                            aux_start = start + relativedelta(months=1)
                                            aux_stop = stop + relativedelta(months=1)

                                    this_date_ok = False

                            self.create_task(aux_date, aux_start, aux_stop)
                        else:
                            date_ok = False

                else:
                    # Specific weekdays
                    date_ok = True
                    if not final_date:
                        final_date = self.get_default_final_date(self.rrule_type, self.interval, self.count)

                    while date_ok:
                        deadline = self.calculate_date(deadline, self.rrule_type, self.interval)
                        start = self.calculate_date(start, self.rrule_type, self.interval)
                        stop = self.calculate_date(stop, self.rrule_type, self.interval)
                        if deadline <= final_date:
                            # Let's get the list of dates for the required weekday
                            aux_weekday = days_by_month.index(self.week_list)
                            aux_days = []
                            aux_starts = []
                            aux_stops = []
                            for d in range(0, monthrange(deadline.year, deadline.month)[1]):
                                aux_date = datetime.date(deadline.year, deadline.month, d + 1)
                                aux_start = start.replace(day=d + 1)
                                aux_stop = stop.replace(day=d + 1)
                                if aux_date.weekday() == aux_weekday:
                                    aux_days.append(aux_date)
                                    aux_starts.append(aux_start)
                                    aux_stops.append(aux_stop)

                            if self.byday == '-1':
                                aux_by_day = -1
                            else:
                                aux_by_day = int(self.byday) - 1

                            aux_deadline = aux_days[aux_by_day]
                            aux_start = aux_starts[aux_by_day]
                            aux_stop = aux_stops[aux_by_day]

                            self.create_task(aux_deadline, aux_start, aux_stop)
                        else:
                            date_ok = False

            elif self.rrule_type == 'weekly' and days_chosen:

                # We add INTERVAL weeks to the last date and create a task on each chosen weekday
                date_ok = True
                while date_ok:
                    deadline = self.calculate_date(deadline, self.rrule_type, self.interval)
                    start = self.calculate_date(start, self.rrule_type, self.interval)
                    stop = self.calculate_date(stop, self.rrule_type, self.interval)
                    deadline_weekday = deadline.weekday()
                    start_weekday = start.weekday()
                    stop_weekday = stop.weekday()

                    if (
                            (self.end_type != ' count' and final_date and deadline <= final_date)
                            or self.end_type == 'count'
                    ):

                        for d in range(0, len(days)):
                            aux_deadline = deadline
                            aux_start = start
                            aux_stop = stop
                            if eval('self.' + days[d]):
                                if deadline_weekday <= d:
                                    days_to_add = (d - deadline_weekday)
                                else:
                                    days_to_add = 7 - (deadline_weekday - d)
                                if start_weekday <= d:
                                    days_to_add = (d - start_weekday)
                                else:
                                    days_to_add = 7 - (start_weekday - d)
                                if stop_weekday <= d:
                                    days_to_add = (d - stop_weekday)
                                else:
                                    days_to_add = 7 - (stop_weekday - d)
                                aux_deadline += relativedelta(days=days_to_add)
                                aux_stop += relativedelta(days=days_to_add)
                                aux_start += relativedelta(days=days_to_add)
                                self.create_task(aux_deadline, aux_start, aux_stop)

                        if self.end_type == 'count':
                            date_ok = False
                    else:
                        date_ok = False

        return True

    @api.multi
    def _get_ics_file(self):
        """ Returns iCalendar file for the event invitation.
            :returns a dict of .ics file content for each meeting
        """
        result = {}

        def ics_datetime(idate, allday=False):
            if idate:
                if allday:
                    return idate
                else:
                    return idate.replace(tzinfo=pytz.timezone('UTC'))
            return False

        try:
            # FIXME: why isn't this in CalDAV?
            import vobject
        except ImportError:
            _logger.warning(
                "The `vobject` Python module is not installed, so iCal file generation is unavailable. Please install the `vobject` Python module")
            return result

        for meeting in self:
            cal = vobject.iCalendar()
            event = cal.add('vevent')

            if not meeting.start or not meeting.stop:
                raise UserError(_("First you have to specify the date of the invitation."))
            event.add('created').value = ics_datetime(fields.Datetime.now())
            event.add('dtstart').value = ics_datetime(meeting.start, meeting.allday)
            event.add('dtend').value = ics_datetime(meeting.stop, meeting.allday)
            event.add('summary').value = meeting.summary
            if meeting.description:
                event.add('description').value = meeting.description
            if meeting.location:
                event.add('location').value = meeting.location
            if meeting.rrule:
                event.add('rrule').value = meeting.rrule

            if meeting.alarm_ids:
                for alarm in meeting.alarm_ids:
                    valarm = event.add('valarm')
                    interval = alarm.interval
                    duration = alarm.duration
                    trigger = valarm.add('TRIGGER')
                    trigger.params['related'] = ["START"]
                    if interval == 'days':
                        delta = timedelta(days=duration)
                    elif interval == 'hours':
                        delta = timedelta(hours=duration)
                    elif interval == 'minutes':
                        delta = timedelta(minutes=duration)
                    trigger.value = delta
                    valarm.add('DESCRIPTION').value = alarm.name or u'Odoo'
            for attendee in meeting.attendee_ids:
                attendee_add = event.add('attendee')
                attendee_add.value = u'MAILTO:' + (attendee.email or u'')
            result[meeting.id] = cal.serialize().encode('utf-8')

        return result

    @api.multi
    def create_attendees_for_meeting(self):
        current_user = self.env.user
        result = {}
        for meeting in self:
            alreay_meeting_partners = meeting.attendee_ids.mapped('partner_id')
            meeting_attendees = self.env['activity.attendee']
            meeting_partners = self.env['res.partner']
            for partner in meeting.partner_ids.filtered(lambda partner: partner not in alreay_meeting_partners):
                values = {
                    'partner_id': partner.id,
                    'email': partner.email,
                    'activity_id': meeting.id,
                }

                # current user don't have to accept his own meeting
                if partner == self.env.user.partner_id:
                    values['state'] = 'accepted'

                attendee = self.env['activity.attendee'].create(values)

                meeting_attendees |= attendee
                meeting_partners |= partner

            if meeting_attendees and not self._context.get('detaching'):
                to_notify = meeting_attendees.filtered(lambda a: a.email != current_user.email)
                to_notify._send_mail_to_attendees('spc_activity.spc_calendar_template_meeting_invitation')

            if meeting_attendees:
                meeting.write({'attendee_ids': [(4, meeting_attendee.id) for meeting_attendee in meeting_attendees]})

            if meeting_partners:
                meeting.message_subscribe(partner_ids=meeting_partners.ids)

            # We remove old attendees who are not in partner_ids now.
            all_partners = meeting.partner_ids
            all_partner_attendees = meeting.attendee_ids.mapped('partner_id')
            old_attendees = meeting.attendee_ids
            partners_to_remove = all_partner_attendees + meeting_partners - all_partners

            attendees_to_remove = self.env["activity.attendee"]
            if partners_to_remove:
                attendees_to_remove = self.env["activity.attendee"].search(
                    [('partner_id', 'in', partners_to_remove.ids), ('activity_id', '=', meeting.id)])
                attendees_to_remove.unlink()

            result[meeting.id] = {
                'new_attendees': meeting_attendees,
                'old_attendees': old_attendees,
                'removed_attendees': attendees_to_remove,
                'removed_partners': partners_to_remove
            }
        return result


    @api.multi
    def get_interval(self, interval, tz=None):
        """ Format and localize some dates to be used in email templates
            :param string interval: Among 'day', 'month', 'dayname' and 'time' indicating the desired formatting
            :param string tz: Timezone indicator (optional)
            :return unicode: Formatted date or time (as unicode string, to prevent jinja2 crash)
        """
        self.ensure_one()
        date = fields.Datetime.from_string(self.start)

        if tz:
            timezone = pytz.timezone(tz or 'UTC')
            date = date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)

        if interval == 'day':
            # Day number (1-31)
            result = pycompat.text_type(date.day)

        elif interval == 'month':
            # Localized month name and year
            result = babel.dates.format_date(date=date, format='MMMM y', locale=self._context.get('lang') or 'en_US')

        elif interval == 'dayname':
            # Localized day name
            result = babel.dates.format_date(date=date, format='EEEE', locale=self._context.get('lang') or 'en_US')

        elif interval == 'time':
            # Localized time
            # FIXME: formats are specifically encoded to bytes, maybe use babel?
            dummy, format_time = self._get_date_formats()
            result = tools.ustr(date.strftime(format_time + " %Z"))

        return result

    @api.multi
    def get_display_time_tz(self, tz=False):
        """ get the display_time of the meeting, forcing the timezone. This method is called from email template, to not use sudo(). """
        self.ensure_one()
        if tz:
            self = self.with_context(tz=tz)
        return self._get_display_time(self.start, self.stop, self.duration, self.allday)

    @api.multi
    def write(self, values):
        # compute duration, only if start and stop are modified
        if not 'duration' in values and 'start' in values and 'stop' in values:
            values['duration'] = self._get_duration(values['start'], values['stop'])

        for meeting in self:
            real_ids = [int(meeting.id)]
            real_meetings = self.browse(real_ids)
            all_meetings = real_meetings
            super(MailActivity, real_meetings).write(values)

            attendees_create = False
            if values.get('partner_ids', False):
                attendees_create = all_meetings.with_context(dont_notify=True).create_attendees_for_meeting()  # to prevent multiple notify_next_alarm
                # managers_create = all_meetings.with_context(dont_notify=True).create_managers()  # to prevent multiple notify_next_alarm

            # Notify attendees if there is an alarm on the modified event, or if there was an alarm
            # that has just been removed, as it might have changed their next event notification
            if not self._context.get('dont_notify'):
                if len(meeting.alarm_ids) > 0 or values.get('alarm_ids'):
                    partners_to_notify = meeting.partner_ids.ids
                    event_attendees_changes = attendees_create and real_ids and attendees_create[real_ids[0]]
                    if event_attendees_changes:
                        partners_to_notify.extend(event_attendees_changes['removed_partners'].ids)
                    self.env['activity.alarm_manager'].notify_next_alarm(partners_to_notify)

            if (values.get('start_date') or values.get('start_datetime') or (values.get('start') and self.env.context.get('from_ui'))) and values.get('active', True):
                for current_meeting in all_meetings:
                    if attendees_create:
                        attendees_create = attendees_create[current_meeting.id]
                        attendee_to_email = attendees_create['old_attendees'] - attendees_create['removed_attendees']
                    else:
                        attendee_to_email = current_meeting.attendee_ids

                    if attendee_to_email:
                        attendee_to_email._send_mail_to_attendees('spc_activity.spc_calendar_template_meeting_changedate')
        return True

    @api.model
    def create(self, values):
        if self._context.get("by_pass"):

            # compute duration, if not given
            if not 'duration' in values:
                values['duration'] = self._get_duration(values['start'], values['stop'])

            activity = super(MailActivity, self).create(values)

        # -----Envoie d'email pour la validation----
            copy_mail = values.get('copy_mail', False)
            if len(activity.user_ids) > 1 and not copy_mail:
                activity.ensure_one()
                template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Envoie email au Manager')], limit=1)
                name_user = ''
                for p in activity.user_ids:
                    name_user = name_user + ',' + p.name
                partner_ids = []
                for obj in activity.activity_type_id.manager_ids:
                    if obj.partner_id.id:
                        partner_ids.append(obj.partner_id.id)

                body_html = '<p>Bonjour '  ',<br />' \
                            ' la tâche %s est assigné à %s . <br />' \
                            'Cette tâche commencera le %s et terminera le %s' \
                            % (activity.summary, name_user, activity.start_datetime,
                               activity.stop_datetime)

                if template_obj:
                    mail_values = {
                        'subject': _('Demande de validation de la tâche: %s') % (activity.summary),
                        'body_html': body_html,
                        'recipient_ids': [(4, pid) for pid in partner_ids],
                    }
                    create_and_send_email = self.env['mail.mail'].create(mail_values).send()
        # ---- répétition de la tâche par récccursivité ----
            copy_reccurent = values.get('copy_reccurent', False)
            if values['reccurrent'] and not copy_reccurent:
                activity.create_repetition()
                values.update({
                    'copy_val': True,
                    'copy_reccurent': True,
                })
        #----multiplication de la tâche pour plusieurs utilisateurs par site----
            copy_val = values.get('copy_val', False)
            if len(activity.user_ids) > 1 and not copy_val and values['by_mass'] == 'individual':
                    for user in activity.user_ids:
                        if activity.user_id.id != user.id:
                            user_copied_id = user.id
                            values.update({
                                'copy_val': True,
                                'user_id': user_copied_id,
                                'copy_mail': True,
                                'copy_reccurent': True,
                            })
                            activity.copy(default=values)

            if values['by_mass'] == 'by_group' and values['group_id'] and not copy_val:
                users_affected = self.env['res.users'].search([('groups_id', 'in', [values['group_id']])])
                if users_affected:
                    values.update({
                        'user_ids': [(6, 0, users_affected.ids)],
                    })
                    for user in users_affected:
                        if activity.user_id.id != user.id:
                            values.update({
                                'user_id': user.id,
                                'copy_val': True,
                            })
                            activity.copy(default=values)


            activity.with_context(dont_notify=True).create_attendees_for_meeting()
            # meeting.with_context(dont_notify=True).create_managers()

        # ----Notify attendees if there is an alarm on the created event, as it might have changed their
            # next event notification----
            if not self._context.get('dont_notify'):
                if len(activity.alarm_ids) > 0:
                    self.env['activity.alarm_manager'].notify_next_alarm(activity.partner_ids.ids)
        else:
            default_res_model = self._context.get('default_res_model')
            default_res_id = self._context.get('default_res_id')
            res_model_id = self.env['ir.model'].search([('model', '=', default_res_model)]).id
            model_name = self._context.get('default_res_model')
            date_deadline = values['date_deadline']
            stop = datetime.datetime.strptime(date_deadline, "%Y-%m-%d")
            values.update({'res_id': default_res_id,
                           'res_model': model_name,
                           'res_model_id': res_model_id,
                           'summary': values['summary'],
                           'activity_type_id': values['activity_type_id'],
                           'date_deadline': values['date_deadline'],
                           'automated': True,
                           # 'start': self._context.get('create_date'),
                           'stop':stop,
                           'resource_ref': '%s,%s' % (default_res_model, default_res_id),

                           })

            activity = super(MailActivity, self.sudo()).create(values)
        return activity

    @api.multi
    def unlink(self):
        return super(MailActivity, self.sudo()).unlink()

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'date' in groupby:
            raise UserError(_('Group by date is not supported, use the calendar view instead.'))
        return super(MailActivity, self.with_context(virtual_id=False)).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if not fields:
            fields = list(self._fields)
        fields2 = fields and fields[:]
        EXTRAFIELDS = ('privacy', 'user_id', 'duration', 'allday', 'start', 'rrule', 'group_ids')
        for f in EXTRAFIELDS:
            if fields and (f not in fields):
                fields2.append(f)

        select = [(x, x) for x in self.ids]
        real_events = self.search([])
        real_data = super(MailActivity, real_events).read(fields=fields2, load=load)
        real_data = dict((d['id'], d) for d in real_data)

        result = []
        for calendar_id, real_id in select:
            if not real_data.get(real_id):
                continue
            res = real_data[real_id].copy()
            res['id'] = calendar_id
            result.append(res)
        # group of user
        current_user = self.env.user.id
        group_current_user = self.env['res.users'].search([('id', '=', current_user)]).groups_id.ids
        for dict_activity in result:
            group_ids = dict_activity['group_ids']
            check = any(item in group_ids for item in group_current_user)

            if dict_activity['user_id']:
                user_id = type(dict_activity['user_id']) in (tuple, list) and dict_activity['user_id'][0] or dict_activity['user_id']
                if user_id == self.env.user.id or (dict_activity['privacy'] == 'by_group' and check is True):
                    continue
            if dict_activity['privacy'] == 'private' or (dict_activity['privacy'] == 'by_group' and check is False):
                for f in dict_activity:
                    recurrent_fields = self._get_recurrent_fields()
                    public_fields = list(set(recurrent_fields + ['id', 'allday', 'start', 'stop', 'display_start', 'display_stop', 'duration', 'state', 'interval', 'count', 'rrule','date_limite']))
                    if f not in public_fields:
                        if isinstance(dict_activity[f], list):
                            dict_activity[f] = []
                        else:
                            dict_activity[f] = False
                    if f == 'summary':
                        dict_activity[f] = _('Busy')

        for dict_activity in result:
            for k in EXTRAFIELDS:
                if (k in dict_activity) and (fields and (k not in fields)):
                    del dict_activity[k]
        return result

    # region Actions
    @api.multi
    def to_validate(self):
        user = self.env.user
        if user:
            if (self.activity_type_id.is_validated is True) and not user.has_group('spc_activity.group_responsable_planification'):
                raise ValidationError('Vous ne pouvez pas valider cette tâche!')
            else:
                return self.write({'workflow_activity': 'validated'})

    @api.multi
    def to_do(self):
        return self.write({'workflow_activity': 'done'})

    @api.multi
    def to_cancel(self):
        return self.write({'workflow_activity': 'canceled'})

    @api.multi
    def to_reset(self):
        return self.write({'workflow_activity': 'new'})

    @api.multi
    def action_to_validate(self):
        for rec in self:
            rec.to_validate()

    @api.multi
    def action_to_do(self):
        for rec in self:
            if rec.workflow_activity == 'validated':
                rec.to_do()

    @api.multi
    def action_sendmail(self):
        email = self.env.user.email
        if email:
            for meeting in self:
                meeting.attendee_ids._send_mail_to_attendees('spc_activity.spc_calendar_template_meeting_invitation')
        return True
    # endregion

    # region Model methods
    # Si la date d'échéance dépasse la date de fin, la tâche passerai automatiquement à l'état terminée.
    @api.depends('stop_datetime')
    def _cron_untreated_activity(self):
        _logger.info("Start CRON Untreated Activity")
        mail_activity_obj = self.search([])
        for act in mail_activity_obj:
            if act.stop_datetime and act.activity_type_id.date_due:
                if act.stop_datetime < act.activity_type_id.date_due and act.state not in ['done', 'canceled', 'untreated']:
                     act.write({'workflow_activity': 'untreated'})
        return

    # Si la date de validation est atteint, la tâche passerai automatiquement à l'état validée.
    def _cron_unvalidated_activity(self):
        _logger.info("Start CRON Unvalidated Activity")
        mail_activity_obj = self.search([])
        now = fields.Datetime.now()
        for act in mail_activity_obj:
            if act.activity_type_id.validation_automatique:
                if act.activity_type_id.date_validation == now:
                    act.write({'workflow_activity': 'validated'})
        return

    @api.model
    def _selection_target_model(self):
        # if self.act_model_id:
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    #endregion


class ActivityType(models.Model):

    _name = 'mail.activity.tags'
    _description = 'Mail Activity Type'

    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    category = fields.Selection(selection_add=[('meeting', 'Meeting')])
    group_ids = fields.Many2many('res.groups', 'res_groups_mail_activity_type_rel', 'mail_activity_type_id', 'group_id',
                                 string='Groupes', help="Ce champs est utilisé pour associé des groupes à une activité.")
    date_due = fields.Datetime("Date d'échéance", help='Ce champs permet la clôture automatique de la tâche')
    is_email = fields.Boolean('Notification par email', index=True)
    model_id = fields.Many2one('ir.model', string="Objet")
    is_validated = fields.Boolean('Validation obligatoire', index=True, help="Si cette case est coché, la validation par le responsable de l'activité devient obligatoire")
    manager_ids = fields.Many2many('res.users', 'mail_activity_type_users_rel', 'mail_activity_type_id', 'user_id', string='Responsables de la taĉhe')
    date_validation = fields.Datetime(string='Date de validation',compute='_compute_date_validation', store=True, help='Ce champs permet la validation automatique de la tâche')
    validation_automatique = fields.Boolean(string="Validation automatique")
    nbr_days_validation = fields.Integer(string="Valider après")
    nbr_hours_validation = fields.Integer()
    resource_ref = fields.Reference(string='Référence', selection='_selection_target_model')
    is_confugirable = fields.Boolean(string="Liée à la réference")

    @api.onchange('is_confugirable')
    def onchange_activity_type(self):
        if self.is_confugirable is False:
            self.resource_ref = False
        else:
            self.model_id = False

    @api.model
    def _selection_target_model(self):
        # if self.act_model_id:
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    @api.depends('create_date', 'nbr_days_validation', 'nbr_hours_validation')
    def _compute_date_validation(self):
        for rec in self:
            rec.date_validation = rec.create_date
            if rec.create_date and (rec.nbr_days_validation or rec.nbr_hours_validation):
                rec.date_validation = rec.create_date + timedelta(days=rec.nbr_days_validation) + timedelta(hours=rec.nbr_hours_validation)
            if not rec.create_date and rec.date_validation:
                rec.date_validation += timedelta(days=rec.nbr_days_validation) + timedelta(hours=rec.nbr_hours_validation)


class ActivityMotif(models.Model):
    _name = 'spc.activity.motif'
    _description = "Activité réinitialisée"

    name = fields.Char(string="Libellé", required=True)


class ActivityReset(models.Model):
    _name = 'spc.activity.reset'
    _description = "Motif d'activité"

    name = fields.Text('Description')
    date_reset = fields.Datetime('Date')
    user_id = fields.Many2one('res.users', 'Utilisateur', default=lambda self: self.env.user, index=True)
    activity_id = fields.Many2one('mail.activity', string='Activité', readonly=True)
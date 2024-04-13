# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    activity_last_notif_ack = fields.Datetime('Last notification marked as read from base Calendar', default=fields.Datetime.now)

    @api.multi
    def get_attendee_detail_activity(self, activity_id):
        """ Return a list of tuple (id, name, status)
            Used by base_activity.js : Many2ManyAttendee
        """
        datas = []
        activity = None
        if activity_id:
            activity = self.env['mail.activity'].browse(activity_id)

        for partner in self:
            data = partner.name_get()[0]
            data = [data[0], data[1], False, partner.color]
            if activity and activity.activity_type_id.category == 'meeting':
                for attendee in activity.attendee_ids:
                    if attendee.partner_id.id == partner.id:
                        data[2] = attendee.state
            datas.append(data)
        return datas

    @api.model
    def _set_activity_last_notif_ack(self):
        partner = self.env['res.users'].browse(self.env.uid).partner_id
        partner.write({'activity_last_notif_ack': datetime.now()})
        return

class ResUsersCalendar(models.Model):
    _name = 'res.users.calendar'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    user_calendar_id = fields.Many2one('res.users', 'Me')
    active = fields.Boolean('Active', default=True)
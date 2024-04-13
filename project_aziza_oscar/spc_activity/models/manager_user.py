# -*- coding: utf-8 -*-
import base64

from odoo import api ,models, fields, _


class Manager(models.Model):
    """ Calendar Manager Information """

    _name = 'manager.user'
    _description = 'Activity Manager Information'

    name = fields.Char('Common name', compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', 'Contact', readonly="True")
    user_id = fields.Many2one('res.users', 'Manager', readonly="True")
    resp_zone_id = fields.Many2one('res.users', 'RZ', readonly="True")
    dre_id = fields.Many2one('res.users', 'DRE', readonly="True")
    email = fields.Char('Email', help="Email of Invited Person")
    activity_id = fields.Many2one('mail.activity', 'Activities linked', ondelete='cascade')

    # à voir ou à supprimer
    # @api.multi
    # def _send_mail_to_managers(self, template_xmlid, force_send=False):
    #     """ Send mail for event invitation to event attendees.
    #         :param template_xmlid: xml id of the email template to use to send the invitation
    #         :param force_send: if set to True, the mail(s) will be sent immediately (instead of the next queue processing)
    #     """
    #     res = False
    #
    #     if self.env['ir.config_parameter'].sudo().get_param('spc_activity.block_mail') or self._context.get("no_mail_to_attendees"):
    #         return res
    #
    #     calendar_view = self.env.ref('spc_activity.spc_mail_activity_view_calendar_inherit')
    #     invitation_template = self.env.ref(template_xmlid)
    #
    #     # get ics file for all meetings
    #     ics_files = self.mapped('activity_id')._get_ics_file()
    #
    #     # prepare rendering context for mail template
    #     colors = {
    #         'needsAction': 'grey',
    #         'accepted': 'green',
    #         'tentative': '#FFFF00',
    #         'declined': 'red'
    #     }
    #     rendering_context = dict(self._context)
    #     rendering_context.update({
    #         'color': colors,
    #         'action_id': self.env['ir.actions.act_window'].search([('view_id', '=', calendar_view.id)], limit=1).id,
    #         # 'action_id': 424,
    #         'dbname': self._cr.dbname,
    #         'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url',
    #                                                                      default='http://localhost:8069')
    #     })
    #     invitation_template = invitation_template.with_context(rendering_context)
    #
    #     # send email with attachments
    #     mails_to_send = self.env['mail.mail']
    #     for attendee in self:
    #         if attendee.email or attendee.partner_id.email:
    #             # FIXME: is ics_file text or bytes?
    #             ics_file = ics_files.get(attendee.activity_id.id)
    #             mail_id = invitation_template.send_mail(attendee.id, notif_layout='mail.mail_notification_light')
    #
    #             vals = {}
    #             if ics_file:
    #                 vals['attachment_ids'] = [(0, 0, {'name': 'invitation.ics',
    #                                                   'mimetype': 'text/calendar',
    #                                                   'datas_fname': 'invitation.ics',
    #                                                   'datas': base64.b64encode(ics_file)})]
    #             vals['model'] = None  # We don't want to have the mail in the tchatter while in queue!
    #             vals['res_id'] = False
    #             current_mail = self.env['mail.mail'].browse(mail_id)
    #             current_mail.mail_message_id.write(vals)
    #             mails_to_send |= current_mail
    #
    #     if force_send and mails_to_send:
    #         res = mails_to_send.send()
    #
    #     return res

from odoo import models, fields, api


class SessionAddAttendees(models.TransientModel):
    _name = 'openacademy.session.add_attendees'

    def _default_sessions(self):
        return self.env['openacademy.session'].browse(self._context.get('active_id'))

    session_ids = fields.Many2many('openacademy.session', string='Session',
                                   required=True, default=_default_sessions)
    attendee_ids = fields.Many2many('res.partner', string='Attendees')

    @api.multi
    def subscribe(self):
        self.session_ids.attendee_ids |= self.attendee_ids
        return {}

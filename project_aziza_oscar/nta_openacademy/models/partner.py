from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    instructor = fields.Boolean('Instructor', default=False)
    session_ids = fields.Many2many('openacademy.session',
                                   column1='attendee_id', column2='session_id',
                                   string='Attended sessions',
                                   readonly=True)

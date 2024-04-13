# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class DispatchReset(models.Model):
    _name = "oscar.dispatch.reset"
    _description = "Remettre Dispatch"

    name = fields.Char('Motif', required=True)
    date_reset = fields.Date('Date')
    user_id = fields.Many2one('res.users', string='Utilisateur')
    dispatch_id = fields.Many2one('oscar.dispatch', string='Dispatch')
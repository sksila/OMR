# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class DerogationReset(models.Model):
    _name = "derogation.reset"
    _description = "Remettre Derogation"

    name = fields.Char('Motif', required=True)
    date_reset = fields.Date('Date')
    user_id = fields.Many2one('res.users', string='Utilisateur')
    derogation_id = fields.Many2one('derogation.derogation', string='Dérogation')

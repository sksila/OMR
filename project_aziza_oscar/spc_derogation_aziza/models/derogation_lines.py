# -*- coding: utf-8 -*-

from odoo import fields, models


class DerogationLine(models.Model):
    _name = "derogation.derogation.line"

    derogation_id = fields.Many2one('derogation.derogation', string='Dérogation')
    magasin_id = fields.Char(string="Magasin")
    quantity = fields.Float(string="Quantité")
    responsable_magasin_id = fields.Many2one('res.users', 'Responsable magasin')
    bon_retour = fields.Char(string="Bon de retour")
    state = fields.Selection(related='derogation_id.state')

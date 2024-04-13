# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

class BRV(models.Model):
    _name = 'oscar.brv'
    _description = 'Bon de Réception valorisé'
    _order = "date_brv desc"

    name = fields.Char('Numéro BRV', required=True, index=True)
    num_cmd = fields.Char('Numéro cmd', index=True)
    date_brv = fields.Datetime('Date BRV', default=fields.Datetime.now, index=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', domain="[('supplier','=', True)]", index=True)
    site_id = fields.Many2one('oscar.site', string='Site', index=True)
    brv_line_ids = fields.One2many('oscar.brv.line', 'brv_id', string='Détails')
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('validated', 'Validé'),
    ], string='Status', index=True, readonly=True, default='new', copy=False)
    active = fields.Boolean(string='Activé', default=True)

class BRVLine(models.Model):
    _name = 'oscar.brv.line'
    _description = 'Détail BRV'

    name = fields.Char('Désignation', related='product_id.name')
    product_id = fields.Many2one('product.template', string='Article', index=True, required=True, ondelete='cascade')
    qte_recue = fields.Float('Qté reçue')
    unite_recue = fields.Char('Unité reçue')
    brv_id = fields.Many2one('oscar.brv', string='BRV', index=True, ondelete='cascade')
# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

class BL(models.Model):
    _name = 'oscar.bl'
    _description = 'Bon de livraison'
    _order = "date_bl desc"

    name = fields.Char('Numéro BL', required=True, index=True)
    date_bl = fields.Datetime('Date BL', default=fields.Datetime.now, index=True)
    client_id = fields.Many2one('oscar.site', string='Client', index=True)
    partner_id = fields.Many2one('res.partner', string='Société', domain="[('supplier','=', True)]", index=True)
    bl_line_ids = fields.One2many('oscar.bl.line', 'bl_id', string='Détails')
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('validated', 'Validé'),
    ], string='Status', index=True, readonly=True, default='new', copy=False)
    active = fields.Boolean(string='Activé', default=True)

class BlLine(models.Model):
    _name = 'oscar.bl.line'
    _description = 'Détail bon de livraison'

    name = fields.Char('Désignation', related='product_id.name')
    product_id = fields.Many2one('product.template', string='Article', index=True, required=True, ondelete='cascade')
    qte_livree = fields.Float('Qté livrée')
    unite_livree = fields.Char('Unité livrée')
    bl_id = fields.Many2one('oscar.bl', string='BL', index=True, ondelete='cascade')
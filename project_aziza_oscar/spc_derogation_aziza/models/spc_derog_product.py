# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class DerogationProduct(models.Model):
    _name = "spc_derog.product"


    derog_product_id = fields.Many2one('derogation.derogation')
    entrepot_id = fields.Many2one('oscar.site', 'Entrepôt', required=True, domain=[('site_type', '=', 'ENTREPOT')])
    qty_derogation = fields.Integer('Qté Totale UVC')
    qty_partielle = fields.Integer('Qté partielle UVC')
    date_reception = fields.Date('Date de réception', required=True)
    state = fields.Selection(related='derog_product_id.state', readonly=True)
    type = fields.Selection(related='derog_product_id.type', readonly=True)


    @api.constrains('qty_derogation')
    def _check_null_value(self):
        for rec in self:
            if (rec.qty_derogation <= 0):
                raise ValidationError(_('Quantité total doit avoir une valeur positif'))



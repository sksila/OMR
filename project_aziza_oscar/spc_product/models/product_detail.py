# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SpcSurveyProductDetail(models.Model):
    _name = 'spc_product.detail'

    _sql_constraints = [
        ('product_product_type_uniq', 'unique (product_id, product_type)',
         'Le produit et son type doivent être unique par produit !'),
    ]


    site_ids = fields.Many2many('oscar.site', 'rel_sites_product_details', string='Site')
    product_id = fields.Many2one('product.template')
    product_type = fields.Many2one('spc_product.type', string="Type", required=True)
    



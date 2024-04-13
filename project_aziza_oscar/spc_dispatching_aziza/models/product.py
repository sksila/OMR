# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductCategory(models.Model):
    _inherit = "product.category"

    dlv_dlc_required = fields.Boolean('DLC obligatoire')

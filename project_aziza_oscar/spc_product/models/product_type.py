# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SpcSurveyProductType(models.Model):
    _name = 'spc_product.type'

    name = fields.Char(string='Nom', required=True)
    



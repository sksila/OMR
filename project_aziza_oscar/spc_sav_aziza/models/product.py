# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Product(models.Model):
    _inherit = 'product.template'
    
    is_sav_product = fields.Boolean('Est un article SAV', related="categ_id.categ_sav",store=True)

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    categ_sav = fields.Boolean('Catégorie SAV',default=False)


    
   

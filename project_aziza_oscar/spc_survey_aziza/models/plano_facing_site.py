from odoo import fields, models, api

class PlanoFacingSite(models.Model):
    _name = 'plano_facing.site'
    _description = 'plano_facing.site'
    _rec_name = 'category_name'

    category_name = fields.Char('Plano category')
    element_level = fields.Char(string="Plano type")
    site_id = fields.Many2one('oscar.site')

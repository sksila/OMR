from odoo import fields, models, api

class SiteInherit(models.Model):
    _inherit = 'oscar.site'

    plano_facing_site_ids = fields.One2many('plano_facing.site','site_id', string="Plano-Facing Details")



# -*- coding: utf-8 -*-

from odoo import api, fields, models

PROFILE_CAISSIER_SELECTION = [
    ('RESPMAG', 'Responsable Magasin'),
    ('ADMAG', 'Adjoint Magasin'),
    ('RESPZONE', 'Responsable Zone'),
    ('DRE', 'DRE'),
]

class Users(models.Model):
    
    _inherit = ['res.users']
    
    profil = fields.Selection(PROFILE_CAISSIER_SELECTION, string='Profile', index=True, default=False)
    magasin_ids = fields.Many2many('oscar.site', 'oscar_user_mg_rel', 'user_id', 'magasin_id', string='Sites')
    magasin_count = fields.Integer(string='Nombre des sites', compute="_compute_magasin_count")
    code_user = fields.Char(string="Code user")

    @api.one
    @api.depends('magasin_ids')
    def _compute_magasin_count(self):
        self.magasin_count = len(self.magasin_ids.ids)
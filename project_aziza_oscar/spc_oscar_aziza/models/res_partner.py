# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class Partner(models.Model):
    _inherit = 'res.partner'

    code = fields.Char(string='Code', index=True)
    driver = fields.Boolean(string='Est un chauffeur', index=True,
                               help="Cochez cette case si ce contact est un chauffeur.")
    customer = fields.Boolean(string='Est un client', index=True,
                              help="Cochez cette case si ce contact est un client.")
    cin = fields.Char(string='C.I.N')
    driver_type = fields.Selection([
        ('aziza', 'Aziza'),
        ('lumiere', 'Lumière'),
        ], string='Type de Chauffeur', index=True)
    code_partner = fields.Char(string="Code partner")
    

    sql_constraints = [
        ('code_unique', 'unique (code)',
         'Le code doit être unique!')
    ]


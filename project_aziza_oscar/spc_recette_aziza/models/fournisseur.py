# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OscarFournisseur(models.Model):
    _inherit = 'res.partner'

    type_tr = fields.Selection([
        ('TR', 'TR'),
        ('CC', 'CC'),
        ], string='Type TR / CC', index=True)
# -*- coding: utf-8 -*-

from odoo import api, fields, models


class OscarSite(models.Model):
    # region Private attributes
    _inherit = "oscar.site"

    counter_ids = fields.One2many('oscar.counter.steg', 'magasin_id', string='Compteurs')

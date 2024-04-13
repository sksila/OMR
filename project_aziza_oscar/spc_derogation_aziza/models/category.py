# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class DerogationCategory(models.Model):
    _name = "derogation.category"
    _description = "Origine"
    _mail_post_access = 'read'
    _order = "id desc"

    name = fields.Char(string='Nom', required=True)

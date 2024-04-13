# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResBank(models.Model):
    _inherit = 'res.bank'

    code_bank = fields.Char(string="Code Banque")

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _rec_name = 'bank_id'
    
    code = fields.Char(string="Code")
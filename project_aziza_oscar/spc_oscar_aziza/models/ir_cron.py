# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ir_cron(models.Model):
    """ Model describing cron jobs (also called actions or tasks).
    """
    _inherit = "ir.cron"
    
    is_oscar = fields.Boolean(string="Oscar Cron")
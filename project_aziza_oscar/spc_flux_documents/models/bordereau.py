# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import json


class Bordereau(models.Model):
    _inherit = 'oscar.bordereau'

    document_ids = fields.Many2many('ir.attachment', 'bordereau_document_rel', 'bordereau_id', 'attachment_id', string='Documents', readonly=True, states={'new': [('readonly', False)]})




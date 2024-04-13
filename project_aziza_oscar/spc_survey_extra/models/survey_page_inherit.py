
from odoo import api, fields, models, _
import ast
import logging

class SurveyExtraPageInherit(models.Model):
    _inherit = "survey.page"

    is_correction = fields.Boolean(string='Correction')



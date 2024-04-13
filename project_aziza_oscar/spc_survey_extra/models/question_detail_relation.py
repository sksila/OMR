import json

from odoo import api, fields, models, _
import logging
import re
import mechanize
from mechanize import Browser
import ast

from odoo.exceptions import ValidationError


class RelationQuestionDetail(models.Model):
    _name = "relation.question_detail"
    _description = "Relation Question/Detail"

    row_id = fields.Many2one("survey.label", string="Row")
    condition = fields.Text(string="Condition")
    details_nb_lines = fields.Text(string="Details lines number")
    question_id = fields.Many2one('survey.question')






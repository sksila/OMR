# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models


class ScoringSyntax(models.TransientModel):
    _name = 'scoring.syntax'
    _description = "Scoring syntaxe"

    scoring_criteria_id = fields.Many2one('spc_survey.scoring.criteria')
    survey_id = fields.Many2one('survey.survey', readonly=True)
    survey_id_int = fields.Integer(related="survey_id.id", string="Survey ID", readonly=True)
    page_id = fields.Many2one('survey.page', readonly=True)
    page_id_int = fields.Integer(related="page_id.id", string="Page ID", readonly=True)
    question_ids = fields.Many2many('survey.question', string="Questions", default=lambda self:self.env.context.get('questions'))
    code = fields.Text('Code', default="while(True):")
    criteria_id_int = fields.Integer(related="scoring_criteria_id.id", string="Criteria ID", readonly=True)

    def add_scoring(self):
        self.scoring_criteria_id.write({
            'code': self.code
        })




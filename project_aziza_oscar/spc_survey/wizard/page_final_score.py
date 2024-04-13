# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models


class PageFinalScore(models.TransientModel):
    _name = 'spc_survey.page_final_score'
    _description = "Score final du page"

    name = fields.Char(name="Title")
    criteria_ids = fields.Many2many('spc_survey.scoring.criteria', string="Criteria")
    scoring_id = fields.Many2one('spc_survey.scoring')

    def save(self):
        self.scoring_id.write({
            'final_score_title' : self.name,
            'final_score_criteria' : [(6, 0, self.criteria_ids.ids)]
        })



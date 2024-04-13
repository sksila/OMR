# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models


class SessionFinalScore(models.TransientModel):
    _name = 'spc_survey.session_final_score'
    _description = "Score final du session"

    name = fields.Char(name="Title")
    session_criteria_ids = fields.Many2many('spc_survey.session_scoring', string="Session scoring Criteria")
    session_id = fields.Many2one('spc_survey.session')

    def save(self):
        self.session_id.write({
            'session_final_score_title' : self.name,
            'session_final_score_criteria' : [(6, 0, self.session_criteria_ids.ids)]
        })



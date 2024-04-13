import logging

from odoo import api, fields, models, _


class SpcSurveyCriteriaInherit(models.Model):
    _inherit = "spc_survey.scoring.criteria"

    is_scale = fields.Boolean(string="scale")
    criteria_type_id = fields.Many2one('spc_survey_extra.criteria_type', string="Criteria type")
    row_ids = fields.Many2many('survey.label', 'rel_scoring_criteria_rows', string="Rows")
    domain_rows_ids = fields.Many2many('survey.label', 'rel_domain_rows_ids',
                                       compute="get_questions_suitable_rows_ids")
    operation = fields.Selection(selection_add=[('count_percentage','count percentage'),('count_total_condition_percentage','count total percentage with same condition'),('average_total', 'total average'),('average_total_condition', 'total average with condition'),('average_denom_max_criteria','average (max of denominator)'),('syntax','syntax')])
    code = fields.Text('Code')




    @api.depends('question_ids', 'question_ids.labels_adv_matrix_rows_ids')
    @api.one
    def get_questions_suitable_rows_ids(self):
        rows = []
        if self.question_ids:
            for question in self.question_ids:
                if question.labels_adv_matrix_rows_ids:
                    for row in question.labels_adv_matrix_rows_ids:
                        rows.append(row.id)
        self.domain_rows_ids = [(6, 0, rows)]


class SpcSurveyScoringInherit(models.Model):
    _inherit = "spc_survey.scoring"

    scale_ids = fields.One2many('spc_survey_extra.scale', 'scoring_id', string="Scale", copy=True)


class SpcSurveyScale(models.Model):
    _name = "spc_survey_extra.scale"
    _description = "Scoring baréme"

    min = fields.Float('Min', digits=(7,4), required=True)
    max = fields.Float('Max', digits=(7,4), required=True)
    score = fields.Integer('Score %', required=True)
    formula = fields.Boolean('Formula')
    symbol = fields.Char('Symbol', default="%")
    scoring_id = fields.Many2one('spc_survey.scoring')
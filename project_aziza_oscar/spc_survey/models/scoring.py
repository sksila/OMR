from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError


class SpcSurveyCriteria(models.Model):
    _name = "spc_survey.scoring.criteria"
    _description = "Critéres de scoring"
    _rec_name = "criteria_name"

    criteria_name = fields.Char('Criteria name', required=True)
    question_ids = fields.Many2many('survey.question', 'rel_scoring_criteria_questions', string="Questions")
    column_ids = fields.Many2many('survey.label', 'rel_scoring_criteria_columns', string="Columns", required=True)
    column_value = fields.Char(string="Value")
    operation = fields.Selection([('sum', 'sum'), ('count', 'count'),('average', 'average'), ('percentage', 'percentage')],
                                 string="Operation", required=True)
    scoring_id = fields.Many2one('spc_survey.scoring')
    page_id = fields.Many2one('survey.page', related="scoring_id.page_id")
    survey_id = fields.Many2one('survey.survey', related="page_id.survey_id")
    domain_columns_ids = fields.Many2many('survey.label', 'rel_domain_columns_ids',
                                          compute="get_questions_suitable_columns_ids")
    domain_rows_ids = fields.Many2many('survey.label', 'rel_domain_rows_ids',
                                          compute="get_questions_suitable_rows_ids")
    coefficient = fields.Float('Coefficient', default=1)
    symbol = fields.Char('Symbol', default='%')



    @api.depends('question_ids', 'question_ids.labels_adv_matrix_cols_ids')
    @api.one
    def get_questions_suitable_columns_ids(self):
        columns = []
        columns_vals = []
        repeated_vals = []
        if self.question_ids:
            for question in self.question_ids:
                if question.labels_adv_matrix_cols_ids:
                    for column in question.labels_adv_matrix_cols_ids:
                        columns.append(column.id)
        self.domain_columns_ids = [(6, 0, columns)]
        if len(self.question_ids) > 1:
            # get columns values
            for col in self.domain_columns_ids:
                columns_vals.append(col.value)
            # get only repeated values
            for value in set(columns_vals):
                if columns_vals.count(value) == len(self.question_ids):
                    repeated_vals.append(value)
            # update columns list with the new list
            columns = []
            for column in self.question_ids[0].labels_adv_matrix_cols_ids:
                if column.value in repeated_vals:
                    columns.append(column.id)
        self.domain_columns_ids = [(6, 0, columns)]

    @api.depends('question_ids', 'question_ids.labels_adv_matrix_rows_ids')
    @api.one
    def get_questions_suitable_rows_ids(self):
        rows = []
        rows_vals = []
        repeated_vals = []
        if self.question_ids:
            for question in self.question_ids:
                if question.labels_adv_matrix_rows_ids:
                    for row in question.labels_adv_matrix_rows_ids:
                        rows.append(row.id)
        self.domain_rows_ids = [(6, 0, rows)]
        if len(self.question_ids) > 1:
            # get rows values
            for row in self.domain_rows_ids:
                rows_vals.append(row.value)
            # get only repeated values
            for value in set(rows_vals):
                if rows_vals.count(value) == len(self.question_ids):
                    repeated_vals.append(value)
            # update rows list with the new list
            rows = []
            for row in self.question_ids[0].labels_adv_matrix_rows_ids:
                if row.value in repeated_vals:
                    rows.append(row.id)
        self.domain_rows_ids = [(6, 0, rows)]

class SpcSurveyScoring(models.Model):
    _name = "spc_survey.scoring"
    _description = "Scoring"

    name = fields.Char(string="name")
    page_id = fields.Many2one('survey.page')
    survey_id = fields.Many2one('survey.survey', related="page_id.survey_id")
    scoring_criteria_ids = fields.One2many('spc_survey.scoring.criteria', 'scoring_id', string="Criteria", copy=True)
    final_score_title = fields.Char('Title', readonly=True)
    final_score_criteria = fields.Many2many('spc_survey.scoring.criteria', 'rel_final_score_criteria',
                                            string="Criteria", readonly=True)
    page_question_ids = fields.Many2many('survey.question', 'rel_domain_page_question_ids',
                                         compute="get_page_question_ids")

    @api.depends('page_id', 'page_id.question_ids')
    def get_page_question_ids(self):
        questions = []
        if self.page_id.question_ids:
            for question in self.page_id.question_ids:
                questions.append(question.id)
        self.page_question_ids = [(6, 0, questions)]

    @api.multi
    def write(self, vals):
        if self.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    def unlink(self):
        if self.env.context.get('default_page_id'):
            if self.env['survey.page'].search([('id','=',self.env.context.get('default_page_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(SpcSurveyScoring, self).unlink()
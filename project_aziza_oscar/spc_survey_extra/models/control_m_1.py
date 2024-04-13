import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ControlMM1(models.Model):
    _name = 'spc_survey_extra.control_m_m1'
    _description = 'Audit Control M & M-1'
    _rec_name = 'question_id'

    question_id = fields.Many2one('survey.question', string="Question", required=True)
    question_or_detail = fields.Selection([('question', 'Question'), ('detail', 'Detail')], default="question",
                                          string="Type", required=True)
    column_id = fields.Many2one('survey.label', string="Column", required=True)
    concerned_questions_ids = fields.Many2many('control_m_m1.concerned', string='Concerned questions')
    survey_id = fields.Many2one('survey.survey')

    question_ids = fields.Many2many('survey.question', compute='_compute_question_ids', store=True)
    columns_ids = fields.Many2many("survey.label", compute='_compute_columns_ids', store=True)

    @api.multi
    @api.depends('survey_id')
    def _compute_question_ids(self):
        for rec in self:
            rec.question_ids = self.env['survey.question'].search([('survey_id','=',rec.survey_id.id)]).ids

    @api.multi
    @api.depends('question_or_detail','question_id')
    def _compute_columns_ids(self):
        for rec in self:
            if rec.question_or_detail == 'question':
                rec.columns_ids = self.env['survey.label'].search([('col_question_id', '=', rec.question_id.id)]).ids
            else:
                rec.columns_ids = self.env['survey.label'].search([('detail_col_question_id', '=', rec.question_id.id)]).ids

    @api.multi
    def write(self, vals):
        if self.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    @api.model
    def create(self, values):
        if self.env.context.get('active_id'):
            if self.env['survey.survey'].search([('id', '=', self.env.context.get('active_id'))]).stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune création à l'état validé"))
        control = super(ControlMM1, self).create(values)
        return control

    @api.multi
    def unlink(self):
        if self.env.context.get('active_id'):
            if self.env['survey.survey'].search(
                    [('id', '=', self.env.context.get('active_id'))]).stage_id == self.env.ref(
                    'survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(ControlMM1, self).unlink()

class ControlMM1ConcernedQuestions(models.Model):
    _name = 'control_m_m1.concerned'
    _description = 'Audit Control M & M-1 Concerned Questions'

    question_id = fields.Many2one('survey.question', string="Question", required=True)
    question_or_detail = fields.Selection([('question', 'Question'), ('detail', 'Detail')], default="question",string="Type", required=True)
    column_id = fields.Many2one('survey.label', string="Column", required=True)

    columns_ids = fields.Many2many("survey.label", compute='_compute_columns_ids', strore=True)

    @api.multi
    @api.depends('question_or_detail', 'question_id')
    def _compute_columns_ids(self):
        for rec in self:
            if rec.question_or_detail == 'question':
                rec.columns_ids = self.env['survey.label'].search([('col_question_id', '=', rec.question_id.id)]).ids
            else:
                rec.columns_ids = self.env['survey.label'].search([('detail_col_question_id', '=', rec.question_id.id)]).ids
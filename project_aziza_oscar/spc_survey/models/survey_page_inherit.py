
from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError


class SpcSurveyPageInherit(models.Model):
    _inherit = "survey.page"

    total_questions = fields.Integer(string='Questions', compute="compute_total_questions")
    page_scoring_ids = fields.One2many('spc_survey.scoring', 'page_id', copy=True)
    duplicated_page = fields.Integer("duplicated page")

    @api.multi
    @api.depends('question_ids')
    def compute_total_questions(self):
        self.total_questions = len(self.question_ids)

    @api.model
    def create(self, values):
        if self.env.context.get('default_survey_id'):
            if self.env['survey.survey'].search([('id','=',self.env.context.get('default_survey_id'))]).stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune création à l'état validé"))
        page = super(SpcSurveyPageInherit, self).create(values)
        # create spc_survey.scoring record
        if not self.env.context.get('cp'):
            self.env['spc_survey.scoring'].sudo().create({
                'name': page.title + ' scoring',
                'page_id': page.id,
            })
        return page

    @api.multi
    def write(self, vals):
        if self.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    @api.multi
    def unlink(self):
        if self.env.context.get('default_survey_id'):
            if self.env['survey.survey'].search([('id', '=', self.env.context.get('default_survey_id'))]).stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(SpcSurveyPageInherit, self).unlink()
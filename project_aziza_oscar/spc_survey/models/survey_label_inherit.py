
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging


class SurveyLabelInherit(models.Model):
    _inherit = "survey.label"

    col_question_id = fields.Many2one('survey.question', string='Question', ondelete='cascade')
    row_question_id = fields.Many2one('survey.question', string='Question 2', ondelete='cascade')

    col_type_resp = fields.Selection([
        ("text", _("Text")),
        ("textarea", _("Multilines text")),
        ("number", _("Number")),
        ("float_number", _("Float number")),
        ("date", _("Date")),
        ("dropdown", _("Dropdown")),
        ("attachment", _("Attachment")),
        ("cam", _("Camera"))], string="type")

    #column fields
    options = fields.Char("options")
    min = fields.Char("min")
    max = fields.Char("max")
    min_date = fields.Date("min date")
    max_date = fields.Date("max date")
    today = fields.Selection([('lte_today','<= today'),
                              ('lt_today','< today'),
                              ('gte_today','>= today'),
                              ('gt_today','> today')], string="today")

    #row fields
    #both

    duplicated_column = fields.Integer('old column')
    duplicated_row = fields.Integer('old row')

    @api.one
    @api.constrains('question_id', 'question_id_2')
    def _check_question_not_empty(self):
        """Ensure that field question_id XOR field question_id_2 is not null"""
        #advanced matrix case
        if self.col_question_id or self.row_question_id:
            return
        else:
            if not bool(self.question_id) != bool(self.question_id_2):
                raise ValidationError(_("A label must be attached to only one question."))


    @api.multi
    def write(self, vals):
        for rec in self:
            if rec.question_id.survey_id.stage_id == self.env.ref('survey.stage_permanent') or rec.question_id_2.survey_id.stage_id == self.env.ref('survey.stage_permanent') or rec.col_question_id.survey_id.stage_id == self.env.ref('survey.stage_permanent') or rec.row_question_id.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune modification à l'état validé"))
            else:
                return super().write(vals)

    @api.model
    def create(self, values):
        if self.env.context.get('default_col_question_id'):
            if self.env['survey.question'].search(
                    [('id', '=', self.env.context.get('default_col_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune création à l'état validé"))
        if self.env.context.get('default_row_question_id'):
            if self.env['survey.question'].search(
                    [('id', '=', self.env.context.get('default_row_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune création à l'état validé"))
        label = super(SurveyLabelInherit, self).create(values)
        return label

    @api.multi
    def unlink(self):
        if self.env.context.get('default_col_question_id'):
            if self.env['survey.question'].search(
                    [('id', '=', self.env.context.get('default_col_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        if self.env.context.get('default_row_question_id'):
            if self.env['survey.question'].search(
                    [('id', '=', self.env.context.get('default_row_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(SurveyLabelInherit, self).unlink()
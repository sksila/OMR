from odoo import api, fields, models, _
import logging

from odoo.exceptions import UserError


class QuestionDisplay(models.Model):
    _name = "question.display"
    _description = "Affichage du question"

    name = fields.Char('Name', required=True)
    columns_ids = fields.One2many("survey.label", "col_question_id", string="Columns", related="question_id.labels_adv_matrix_cols_ids", readonly=False)
    rows_ids = fields.One2many("survey.label", "row_question_id", string="Rows", related="question_id.labels_adv_matrix_rows_ids", readonly=False)
    question_id = fields.Many2one('survey.question')
    is_auto_fill = fields.Boolean(related="question_id.fill_auto")
    show_hide_cond_ids = fields.One2many('display.show_hide_cond','question_display_id',string='Show/Hide by condition', copy=True)
    #anomaly
    # anomaly_col_id = fields.Many2one("survey.label", string="Anomaly column")
    # anomaly_values = fields.Char("Anomaly values")

    anomaly_columns_ids = fields.One2many('anomaly.columns','question_display_id', string="Correction lines", copy=True)
    rows2_ids = fields.One2many("survey.label", "row_question_id", string="Rows",
                               related="question_id.labels_adv_matrix_rows_ids", readonly=False)

    @api.multi
    def write(self, vals):
        if self.question_id.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    @api.multi
    def unlink(self):
        if self.env.context.get('default_question_id'):
            if self.env['survey.question'].search([('id', '=', self.env.context.get('default_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(QuestionDisplay, self).unlink()

class AnomalyColumns(models.Model):
    _name = "anomaly.columns"
    _description = "Colonnes d'anomalies"

    anomaly_col_id = fields.Many2one("survey.label", string="Correction Column")
    anomaly_values = fields.Char("Values")
    question_display_id = fields.Many2one('question.display')

class ShowHideCondition(models.Model):
    _name = "display.show_hide_cond"
    _description = "Affichage/Masquage du question"

    row_id = fields.Many2one("survey.label", string='Row')
    column_id = fields.Many2one("survey.label", string="Column", required=True)
    type = fields.Selection([('same_line', 'Same line'), ('different_line', 'Different line')],string='Type', default='same_line')
    condition = fields.Char(string="Condition", required=True)
    concerned_rows = fields.Many2many("survey.label", string="Concerned Rows")
    question_display_id = fields.Many2one('question.display')

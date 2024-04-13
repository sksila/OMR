
from odoo import api, fields, models, _
import logging

from odoo.exceptions import ValidationError


class SurveyExtraLabelInherit(models.Model):
    """
        model : used with model_id field for model type column
        field_model : used with equivalent_field_id for the automating lines filling
    """
    _inherit = "survey.label"

    col_type_resp = fields.Selection(selection_add=[("model", _("Model")),("field_model", _("Field model"))])
    equivalent_field_id = fields.Many2one("ir.model.fields", string="Equivalent")
    model_id = fields.Many2one("ir.model", string="Model")

    data_correction = fields.Boolean('Data Correction')
    display_cols = fields.Char('Columns')
    display_cols_text = fields.Char('Columns')
    row_dropdown_options = fields.Char('Dropdown options')

    note_options = fields.Char('Note options')

    detail_col_question_id = fields.Many2one('survey.question', string='Question column', ondelete='cascade')

    label = fields.Char('label') #etiquette
    model_filter_field_id = fields.Many2one("ir.model.fields", string="Filter field")
    model_filter_list_ids = fields.Many2many("ir.model.fields")

    detail_duplicated_column = fields.Integer('old detail column')


    @api.onchange('model_id')
    def get_model_fields(self):
        if self.model_id:
            fields = self.model_id.fields_get()
            obj = self.env['ir.model.fields'].search([('model_id', '=', self.model_id.id)])
            list = []
            for rec in obj:
                list.append(rec.id)
            self.model_filter_list_ids = [(6, 0, list)]
        else:
            pass

    @api.one
    @api.constrains('question_id', 'question_id_2')
    def _check_question_not_empty(self):
        """Ensure that field question_id XOR field question_id_2 is not null"""
        # advanced matrix case
        if self.col_question_id or self.row_question_id or self.detail_col_question_id:
            return
        else:
            if not bool(self.question_id) != bool(self.question_id_2):
                raise ValidationError(_("A label must be attached to only one question."))
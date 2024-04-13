import json

from odoo import api, fields, models, _
import logging
import re
import mechanize
from mechanize import Browser
import ast

from odoo.exceptions import ValidationError, UserError


class ColumnDependency(models.Model):
    _name = "column.dependency"
    _description = "Dépendances des colonnes"
    _rec_id = "column_id"

    column_id = fields.Many2one("survey.label", string="Column")
    condition = fields.Text(string="Condition", help='Applied this rule for calculation .You can specify condition like AN = 1.')
    result = fields.Char(string="Result")
    reverse_result = fields.Char(string="Reverse result")
    col_calculation_id = fields.Many2one('column.calculation')

    @api.one
    @api.constrains("condition")
    def verify_condition(self):
        if self.condition:
            br = Browser()
            br.set_handle_robots(False)
            br.open('https://infoheap.com/javascript-validate-online/')
            br.select_form(id="form1")
            br['param1'] = self.condition
            response = br.submit()
            response = response.read()
            if '"retcode":"1"' in str(response):
                raise ValidationError(_(self.condition + "  => condition is not valid!"))


class RowColumnDependency(models.Model):
    _name = "row_column.dependency"
    _description = "Dépendances des lignes/colonnes"
    _rec_id = "row_id"

    row_id = fields.Many2one("survey.label", string="Row")
    column_id = fields.Many2one("survey.label", string="Column")
    condition = fields.Text(string="Condition", help='Applied this rule for calculation .You can specify condition like AN = 1.')
    result = fields.Char(string="Result")
    reverse_result = fields.Char(string="Reverse result")
    col_calculation_id = fields.Many2one('column.calculation')

    @api.one
    @api.constrains("condition")
    def verify_condition(self):
        if self.condition:
            br = Browser()
            br.set_handle_robots(False)
            br.open('https://infoheap.com/javascript-validate-online/')
            br.select_form(id="form1")
            br['param1'] = self.condition
            response = br.submit()
            response = response.read()
            if '"retcode":"1"' in str(response):
                raise ValidationError(_(self.condition + "  => condition is not valid!"))



class ColumnCalculation(models.Model):
    _name = "column.calculation"
    _description = "Dépendances du question"

    name = fields.Char(string="name")
    question_id = fields.Many2one('survey.question')
    columns_ids = fields.One2many("survey.label", "col_question_id", string="Columns",
                                  related="question_id.labels_adv_matrix_cols_ids", readonly=False)
    dependency_ids = fields.One2many('column.dependency', 'col_calculation_id', string="Dependencies", copy=True)

    rows_ids = fields.One2many("survey.label", "row_question_id", string="Rows",
                                  related="question_id.labels_adv_matrix_rows_ids", readonly=False)
    row_dependency_ids = fields.One2many('row_column.dependency', 'col_calculation_id', string="Dependencies", copy=True)

    @api.multi
    def write(self, vals):
        if self.question_id.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    @api.multi
    def unlink(self):
        if self.env.context.get('default_question_id'):
            if self.env['survey.question'].search(
                    [('id', '=', self.env.context.get('default_question_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(ColumnCalculation, self).unlink()



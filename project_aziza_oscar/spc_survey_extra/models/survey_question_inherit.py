import json

from odoo import api, fields, models, _
import ast
import logging

class SurveyExtraQuestionInherit(models.Model):
    _inherit = "survey.question"

    fill_auto = fields.Boolean(string="Automatic filling")
    model_id = fields.Many2one(comodel_name="ir.model", string="Model")
    limit = fields.Integer(string='limit')
    model_fields_ids = fields.Many2many("ir.model.fields", string="Fields")

    #filter fields
    filter_domain = fields.Char(string='Filter')
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True, store=True)

    add_line_feature = fields.Boolean(string='Add line feature')
    detail = fields.Boolean(string="Details")
    detail_labels_adv_matrix_cols_ids = fields.One2many("survey.label", "detail_col_question_id", string="Details Columns", copy=True)

    question_detail_relation_ids = fields.One2many('relation.question_detail','question_id',string='Relation Question/Detail' ,copy=True)

    question_dependencies_ids = fields.One2many('column.calculation','question_id', copy=True)
    question_display_ids = fields.One2many('question.display','question_id', copy=True)

    @api.constrains('limit')
    def check_limit_minimum_constraint(self):
        if self.limit < 0:
            old_limit = self.limit
            self.limit = 0
            raise models.ValidationError(
                _("limit should be an integer >= 0 , " + str(old_limit) + " is a bad choice !"))

    @api.onchange('limit')
    def check_limit_minimum(self):
        self.check_limit_minimum_constraint()


    @api.onchange('model_id')
    def onchange_model_fields_ids(self):
        if self.model_id:
            # self.model_name = self.model_id.model #used in domain widget
            obj = self.env['ir.model.fields'].search([('model_id','=',self.model_id.id)])
            list = []
            for rec in obj:
                list.append(rec.id)
            self.model_fields_ids = [(6,0, list)]
        else:
            pass

    def filter_domain_refact(self,domain):
        result = '[]'
        if domain:
            result = domain
            list = [
                ('"','\''),
            ]
            for rec in list:
                result = result.replace(rec[0],rec[1])
        result = ast.literal_eval(result)
        return result


    @api.model
    def create(self, values):
        question = super(SurveyExtraQuestionInherit, self).create(values)
        # create question.display record
        if not self.env.context.get('cp'):
            self.env['question.display'].sudo().create({
                'name' : question.question + ' display',
                'question_id' : question.id,
            })
        # create column.calculation record
        if not self.env.context.get('cp'):
            self.env['column.calculation'].sudo().create({
                'name': question.question + ' columns dependencies',
                'question_id': question.id,
            })
        return question


    def prepare_dependencies(self,dependency_ids):
        key_values = {}
        values = {}
        for rec in dependency_ids:
            key_values = {'column': rec.column_id.value,
                          'condition' : rec.condition,
                          'result' : rec.result,
                          'reverse_result' : rec.reverse_result}
            if rec.column_id.value in values:
                values[rec.column_id.value + str(rec.id)] = key_values
            else:
                values[rec.column_id.value] = key_values
        return json.dumps(values)

    def column_type_field_model_value(self,rec):
        if 'odoo.api' in str(type(rec)): #many2one
            return rec.name
        return rec

    def prepare_row_dependencies(self,row_dependency_ids):
        key_values = {}
        values = {}
        for rec in row_dependency_ids:
            key_values = {'row': rec.row_id.value,
                          'column': rec.column_id.value,
                          'condition': rec.condition,
                          'result': rec.result,
                          'reverse_result': rec.reverse_result}
            if rec.row_id.value in values:
                values[rec.row_id.value + str(rec.id)] = key_values
            else:
                values[rec.row_id.value] = key_values
        return json.dumps(values)

    def get_anomaly_columns(self,anomaly_columns_ids):
        dict_anomalies = {}
        if anomaly_columns_ids:
            for anomaly in anomaly_columns_ids:
                dict_anomalies[anomaly.anomaly_col_id.id] = anomaly.anomaly_values
            return dict_anomalies
        return {}

    def prepare_question_detail_relation(self,question_detail_relation_ids):
        key_values = {}
        values = {}
        for rec in question_detail_relation_ids:
            key_values = {'row': rec.row_id.value,
                          'condition' : rec.condition,
                          'details_nb_lines' : rec.details_nb_lines}
            if rec.row_id.value in values:
                values[rec.row_id.value + str(rec.id)] = key_values
            else:
                values[rec.row_id.value] = key_values
        return json.dumps(values)

    def prepare_show_hide_cond_lines(self,show_hide_cond_ids):
        key_values = {}
        values = {}
        for rec in show_hide_cond_ids:
            key_values = {'row': rec.row_id.value,
                          'column': rec.column_id.value,
                          'type': rec.type,
                          'concerned_rows': [rec.value for rec in rec.concerned_rows],
                          'condition': rec.condition}
            if rec.row_id.value in values:
                values[rec.row_id.value + str(rec.id)] = key_values
            else:
                values[rec.row_id.value] = key_values
        return json.dumps(values)
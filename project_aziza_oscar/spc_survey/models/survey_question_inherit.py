import logging
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SurveyQuestionInherit(models.Model):
    _inherit = "survey.question"

    type = fields.Selection(selection_add=[("advanced_matrix", "Advanced matrix")], default="advanced_matrix")
    labels_adv_matrix_cols_ids = fields.One2many("survey.label", "col_question_id", string="Columns", copy=True)
    labels_adv_matrix_rows_ids = fields.One2many("survey.label", "row_question_id", string="Rows", copy=True)
    cols_count = fields.Integer(compute="_cols_count")
    duplicated_question = fields.Integer('survey.question')


    @api.depends('labels_adv_matrix_cols_ids')
    def _cols_count(self):
        self.cols_count= len(self.labels_adv_matrix_cols_ids)


    # filling the advanced matrix is required
    @api.multi
    def validate_advanced_matrix(self, post, answer_tag):
        errors = {}
        answer = ''
        for key in post:
            if key.startswith(answer_tag) and '_columns_dependencies' not in key and '_rows_columns_dependencies' not in key and '_comment' not in key and key not in post['display_none']:
                answer = post[key]
                # if '<FileStorage' not in answer:
                #     answer = post[key].strip()
                if self.constr_mandatory and not answer:
                    errors.update({answer_tag: self.constr_error_msg + '<span class="d-none">' + key + '</span>'})
                    break

        return errors

    def get_value(self,user_input_line_ids,prefix,user_input_id):
        attach_list = []
        for line in user_input_line_ids:
            if line.a_tag == prefix:
                if line.type_resp == 'attachment' and line.value_adv_mat_attachment:
                    for attach in line.value_adv_mat_attachment:
                        attach_list.append((attach.datas_fname,str(attach.id)))
                    return attach_list
                return line.value_adv_mat
        return ''

    def date_today(self,val):
        if val == 'lte_today':
            return fields.Date.today() + timedelta(days=1)
        elif val == 'lt_today':
            return fields.Date.today()
        elif val == 'gte_today':
            return fields.Date.today()
        elif val == 'gt_today':
            return fields.Date.today() + timedelta(days=1)
        else:
            return ''

    def check_anomaly_row(self,user_input_id,survey_session_info_id,question,row_label):
        column_vals = []
        row_labels = []
        empty_rows = True
        list = []
        anomalies_report_ids = self.env['spc_survey.anomalies.report'].search([('survey_session_id','=',survey_session_info_id.survey_session_id.id),('question_id','=',question.id)])
        for rec in anomalies_report_ids:
            if rec.row_ids:
                if row_label.id in rec.row_ids.ids:
                    row_labels = [row_label.value]
            else:
                row_labels = [row.value for row in question.labels_adv_matrix_rows_ids]
            column_vals.append(rec.column_value)
            list.append((row_labels,rec.column_id.value,column_vals))
            row_labels = []
            column_vals = []
        for rec in list:
            line = self.env['survey.user_input_line'].search([('user_input_id','=',user_input_id.id),('question_id','=',question.id),('row', '=', row_label.value),('column','=',rec[1]),('value_adv_mat','in',rec[2])], limit=1)
            if line:
                return ''
        return 'display:none;'

    def check_anomaly_question(self,user_input_id,survey_session_info_id,question):
        column_vals = []
        row_labels = []
        list = []
        anomalies_report_ids = self.env['spc_survey.anomalies.report'].search([('survey_session_id','=',survey_session_info_id.survey_session_id.id),('question_id','=',question.id)])
        if not anomalies_report_ids:
            return 'display:none;'
        for rec in anomalies_report_ids:
            if rec.row_ids:
                row_labels = [row.value for row in rec.row_ids]
            else:
                row_labels = [row.value for row in question.labels_adv_matrix_rows_ids]
            column_vals.append(rec.column_value)
            list.append((row_labels,rec.column_id.value,column_vals))
            row_labels = []
            column_vals = []
        for rec in list:
            line = self.env['survey.user_input_line'].search([('user_input_id','=',user_input_id.id),('question_id','=',question.id),('row', 'in', rec[0]),('column','=',rec[1]),('value_adv_mat','in',rec[2])], limit=1)
            if line:
                return ''
        return 'display:none;'

    @api.multi
    def write(self, vals):
        if self.survey_id.stage_id == self.env.ref('survey.stage_permanent'):
            raise UserError(_("Aucune modification à l'état validé"))
        else:
            return super().write(vals)

    @api.model
    def create(self, values):
        if self.env.context.get('default_page_id'):
            if self.env['survey.page'].search([('id','=',self.env.context.get('default_page_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune création à l'état validé"))
        question = super(SurveyQuestionInherit, self).create(values)
        return question

    @api.multi
    def unlink(self):
        if self.env.context.get('default_page_id'):
            if self.env['survey.page'].search([('id','=',self.env.context.get('default_page_id'))]).survey_id.stage_id == self.env.ref('survey.stage_permanent'):
                raise UserError(_("Aucune suppression à l'état validé"))
        return super(SurveyQuestionInherit, self).unlink()
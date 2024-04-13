import logging

from odoo import api, fields, models, _


class SpcSurveyُExtraInherit(models.Model):
    _inherit = "survey.survey"

    control_m_m1_ids = fields.One2many('spc_survey_extra.control_m_m1','survey_id', copy=True)

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        default.update(copied_from_id=self.id)
        result = super(SpcSurveyُExtraInherit, self.with_context(cp=True, copied_from_id=self.id)).copy(default=default)
        copied_from_id = self.env['survey.survey'].search([('id', '=', result.id)]).copied_from_id

        for rec in self.env['survey.page'].search([('survey_id', '=', result.id)]):
            for rec2 in self.env['survey.page'].search([('survey_id', '=', copied_from_id.id)]):
                if rec.title == rec2.title:
                    rec.write({'duplicated_page': rec2.id})

        for rec in self.env['survey.question'].search([('survey_id', '=', result.id)]):
            for rec2 in self.env['survey.question'].search([('survey_id', '=', copied_from_id.id)]):
                if rec.question == rec2.question and rec.page_id.title == rec2.page_id.title:
                    rec.write({'duplicated_question': rec2.id})

        for rec in self.env['survey.label'].search(
                [('col_question_id', 'in', self.env['survey.question'].search([('survey_id', '=', result.id)]).ids)]):
            for rec2 in self.env['survey.label'].search([('col_question_id', 'in', self.env['survey.question'].search(
                    [('survey_id', '=', copied_from_id.id)]).ids)]):
                if rec.value == rec2.value and rec.col_question_id.question == rec2.col_question_id.question:
                    rec.write({'duplicated_column': rec2.id})

        for rec in self.env['survey.label'].search(
                [('row_question_id', 'in', self.env['survey.question'].search([('survey_id', '=', result.id)]).ids)]):
            for rec2 in self.env['survey.label'].search([('row_question_id', 'in', self.env['survey.question'].search(
                    [('survey_id', '=', copied_from_id.id)]).ids)]):
                if rec.value == rec2.value and rec.row_question_id.question == rec2.row_question_id.question:
                    rec.write({'duplicated_row': rec2.id})

        for rec in self.env['survey.label'].search([('detail_col_question_id', 'in', self.env['survey.question'].search(
                [('survey_id', '=', result.id)]).ids)]):
            for rec2 in self.env['survey.label'].search([('detail_col_question_id', 'in',
                                                          self.env['survey.question'].search(
                                                                  [('survey_id', '=', copied_from_id.id)]).ids)]):
                if rec.value == rec2.value and rec.detail_col_question_id.question == rec2.detail_col_question_id.question:
                    rec.write({'detail_duplicated_column': rec2.id})

        # example detail_relat
        my_rows = []
        my_cols = []
        my_detail_cols = []
        for question in self.env['survey.question'].search([('survey_id', '=', result.id)]):
            my_rows = dict([(row.duplicated_row, row.id) for row in question.labels_adv_matrix_rows_ids])
            my_cols = dict([(col.duplicated_column, col.id) for col in question.labels_adv_matrix_cols_ids])
            my_detail_cols = dict(
                [(col.detail_duplicated_column, col.id) for col in question.detail_labels_adv_matrix_cols_ids])
            if question.question_detail_relation_ids:
                for line in question.question_detail_relation_ids:
                    if my_rows[line.row_id.id]:
                        line.write({'row_id': my_rows[line.row_id.id]})

            if question.labels_adv_matrix_rows_ids:  # display : show/hide display_cols
                for line in question.labels_adv_matrix_rows_ids:
                    updated_cols_list = []
                    if line.display_cols:
                        for c in line.display_cols.split(","):
                            if my_cols[int(c)]:
                                updated_cols_list.append(str(my_cols[int(c)]))
                        line.write({'display_cols': ",".join(updated_cols_list)})
                        updated_cols_list = []

            display = self.env['question.display'].search([('question_id', '=', question.id)])
            if display.show_hide_cond_ids:
                for line in display.show_hide_cond_ids:
                    if my_rows[line.row_id.id]:
                        line.write({'row_id': my_rows[line.row_id.id]})
                    if my_cols[line.column_id.id]:
                        line.write({'column_id': my_cols[line.column_id.id]})
                    for r in line.concerned_rows:
                        if my_rows[r.id]:
                            line.write({'concerned_rows': [(3, r.id), (4, my_rows[r.id])]})
            if display.anomaly_columns_ids:
                for line in display.anomaly_columns_ids:
                    if my_cols[line.anomaly_col_id.id]:
                        line.write({'anomaly_col_id': my_cols[line.anomaly_col_id.id]})

            dependency = self.env['column.calculation'].search([('question_id', '=', question.id)])
            if dependency.dependency_ids:
                for line in dependency.dependency_ids:
                    if my_cols[line.column_id.id]:
                        line.write({'column_id': my_cols[line.column_id.id]})
            if dependency.row_dependency_ids:
                for line in dependency.row_dependency_ids:
                    if my_rows[line.row_id.id]:
                        line.write({'row_id': my_rows[line.row_id.id]})
                    if my_cols[line.column_id.id]:
                        line.write({'column_id': my_cols[line.column_id.id]})

            control_mm1 = self.env['spc_survey_extra.control_m_m1'].search(
                [('survey_id', '=', result.id), ('question_id', '=', question.duplicated_question)])
            for line in control_mm1:
                line.write({'question_id': question.id})
                if line.question_or_detail == 'question':
                    if my_cols[line.column_id.id]:
                        line.write({'column_id': my_cols[line.column_id.id]})
                else:  # line.question_or_detail == 'detail'
                    if my_detail_cols[line.column_id.id]:
                        line.write({'column_id': my_detail_cols[line.column_id.id]})
                new_concerned_line_dict = {}
                for q in line.concerned_questions_ids:
                    if q.question_id.id == question.duplicated_question:
                        new_concerned_line_dict = {'question_id': question.id}
                        if q.question_or_detail == 'question':
                            if my_cols[q.column_id.id]:
                                new_concerned_line_dict['column_id'] = my_cols[q.column_id.id]
                        else:  # line.question_or_detail == 'detail'
                            if my_detail_cols[q.column_id.id]:
                                new_concerned_line_dict['column_id'] = my_detail_cols[q.column_id.id]
                    new_concerned_line_dict['question_or_detail'] = q.question_or_detail
                    concerned_ques_id = self.env['control_m_m1.concerned'].create(new_concerned_line_dict)
                    new_concerned_line_dict = {}
                    line.write({'concerned_questions_ids': [(3, q.id), (4, concerned_ques_id.id)]})

            my_rows = []
            my_cols = []
            my_detail_cols = []

        scoring = self.env['spc_survey.scoring'].search([('survey_id', '=', result.id)])
        questions = []
        updated_questions = []
        columns = []
        updated_cols = []
        rows = []
        updated_rows = []
        if scoring.scoring_criteria_ids:
            for line in scoring.scoring_criteria_ids:
                questions = [question.id for question in line.question_ids]
                columns = [column.id for column in line.column_ids]
                rows = [row.id for row in line.row_ids]
                updated_questions = self.env['survey.question'].search(
                    [('survey_id', '=', result.id), ('duplicated_question', 'in', questions)]).ids
                line.write({'question_ids': [(6, 0, updated_questions)]})
                updated_rows = self.env['survey.label'].search(
                    [('row_question_id', 'in', self.env['survey.question'].search([('survey_id', '=', result.id)]).ids),
                     ('duplicated_row', 'in', rows)]).ids
                line.write({'row_ids': [(6, 0, updated_rows)]})
                updated_cols = self.env['survey.label'].search(
                    [('col_question_id', 'in', self.env['survey.question'].search([('survey_id', '=', result.id)]).ids),
                     ('duplicated_column', 'in', columns)]).ids
                line.write({'column_ids': [(6, 0, updated_cols)]})
                updated_questions = []
                questions = []
                updated_cols = []
                columns = []
                updated_rows = []
                rows = []

        return result
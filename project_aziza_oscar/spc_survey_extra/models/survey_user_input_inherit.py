import base64
import logging

from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _


class SurveyExtraUserInputInherit(models.Model):
    _inherit = "survey.user_input"
    # _inherit = ['survey.user_input', 'mail.thread', 'mail.activity.mixin']

    is_correction_done = fields.Boolean(string='Correction done?', default=False)

    def extract_surveys_to_correct(self, surveys_reponses):
        list = []
        for surv_rep in surveys_reponses:
            for page in surv_rep.survey_id.page_ids:
                if page.is_correction:
                    list.append(surv_rep.id)
        surveys_reponses = surveys_reponses.search([('id', 'in', list)])
        return surveys_reponses

    def calculate_scores(self):
        final_score_criteria = []
        criteria_list = []
        criteria_type_list = []
        current_criteria_type = ""
        for page in self.survey_id.page_ids:
            for crit in self.env['spc_survey.scoring'].search([('page_id', '=', page.id)]).final_score_criteria:
                final_score_criteria.append(crit.id)
            for criteria in self.env['spc_survey.scoring'].search([('page_id', '=', page.id)]).scoring_criteria_ids:
                criteria_list.append(criteria.id)
                criteria_type_list.append(criteria.criteria_type_id.id)
            criteria_type_list = list(set(criteria_type_list))
            for criteria_type in self.env['spc_survey_extra.criteria_type'].search([('id', 'in', criteria_type_list)]):
                for criteria in self.env['spc_survey.scoring'].search([('page_id', '=', page.id)]).scoring_criteria_ids:
                    if criteria_type.name == criteria.criteria_type_id.name:
                        try:
                            scorer = getattr(self, 'calculate_type_' + str(criteria.operation))
                        except AttributeError:
                            logging.error("No scoring function for this criteria")
                            return False
                        else:
                            result = scorer(criteria, page, page.survey_id)
                            if len(self.criteria_ids.search([('display_type', '!=', 'line_section')])) != len(
                                    self.env['spc_survey.scoring'].search(
                                        [('page_id', '=', page.id)]).scoring_criteria_ids):
                                if current_criteria_type != criteria.criteria_type_id.name:
                                    current_criteria_type = criteria.criteria_type_id.name
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_type_id.name,
                                                                 'display_type': 'line_section'})]
                                    })

                                if criteria.operation in ['percentage'] and not criteria.is_scale:
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id': page.id,
                                                                 'is_final': criteria.id in final_score_criteria,
                                                                 'score_float': round(result),
                                                                 'score_text': str(round(result)) + criteria.symbol,
                                                                 'criteria_id': criteria.id,
                                                                 'coefficient': criteria.coefficient
                                                                 })]
                                    })
                                    continue

                                if criteria.operation in ['count_percentage']:
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id': page.id,
                                                                 'is_final': criteria.id in final_score_criteria,
                                                                 'score_float': round(result),
                                                                 'score_text': str(round(result)) + criteria.symbol,
                                                                 'criteria_id': criteria.id,
                                                                 'coefficient':criteria.coefficient})]
                                    })
                                    continue

                                if criteria.operation in ['count_total_condition_percentage'] and not criteria.is_scale:
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id': page.id,
                                                                 'is_final': criteria.id in final_score_criteria,
                                                                 'score_float': round(result),
                                                                 'score_text': str(round(result)) + criteria.symbol,
                                                                 'criteria_id': criteria.id,
                                                                 'coefficient':criteria.coefficient})]
                                    })
                                    continue

                                if criteria.operation in ['average_denom_max_criteria'] and not criteria.is_scale:
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id': page.id,
                                                                 'is_final': criteria.id in final_score_criteria,
                                                                 'score_float': round(result),
                                                                 'score_text': str(round(result)) + criteria.symbol,
                                                                 'criteria_id': criteria.id,
                                                                 'coefficient':criteria.coefficient})]
                                    })
                                    continue

                                if criteria.operation in ['average_total', 'average_total_condition'] and not criteria.is_scale:
                                    self.sudo().write({
                                        'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id': page.id,
                                                                 'is_final': criteria.id in final_score_criteria,
                                                                 'score_float': result,
                                                                 'score_text': str(result),
                                                                 'criteria_id': criteria.id,
                                                                 'coefficient':criteria.coefficient})]
                                    })
                                    continue

                                if criteria.operation == 'syntax' and not criteria.is_scale:
                                    self.sudo().write({'criteria_ids': [(0, 0, {'name': criteria.criteria_name,
                                                                         'page_id': page.id,
                                                                         'is_final': criteria.id in final_score_criteria,
                                                                         'score_float': result,
                                                                         'score_text': str(result) + criteria.symbol,
                                                                         'criteria_id': criteria.id,
                                                                         'coefficient':criteria.coefficient})]})

                                    continue
                                else:
                                    if criteria.is_scale:
                                        for scale in self.env['spc_survey.scoring'].search([('page_id', '=', page.id)]).scale_ids:
                                            if scale.formula:
                                                if result >= scale.min and result <= scale.max:
                                                    self.sudo().write({'criteria_ids': [(0, 0, {'name': criteria.criteria_name,
                                                                                         'page_id': page.id,
                                                                                         'is_final': criteria.id in final_score_criteria,
                                                                                         'score_float': round(result),
                                                                                         'score_text': str(
                                                                                             round(result)) + criteria.symbol,
                                                                                         'criteria_id': criteria.id,
                                                                                         'coefficient':criteria.coefficient})]})
                                                    break
                                            else:
                                                if result >= scale.min and result <= scale.max:
                                                    self.sudo().write({'criteria_ids': [(0, 0, {'name': criteria.criteria_name,
                                                                                         'page_id': page.id,
                                                                                         'is_final': criteria.id in final_score_criteria,
                                                                                         'score_float': scale.score,
                                                                                         'score_text': str(scale.score) + str(scale.symbol),
                                                                                         'criteria_id': criteria.id,
                                                                                         'coefficient':criteria.coefficient})]})
                                    else:
                                        self.sudo().write({'criteria_ids': [(0, 0,
                                                                      {'name': criteria.criteria_name,
                                                                       'page_id': page.id,
                                                                       'is_final': criteria.id in final_score_criteria,
                                                                       'score_float': round(result),
                                                                       'score_text': str(round(result)),
                                                                       'criteria_id': criteria.id,
                                                                       'coefficient':criteria.coefficient})]})

    def check_row(self, rows):
        rows_values = []
        for row in rows:
            rows_values.append(row.value)
        return rows_values

    def calculate_type_sum(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        if criteria.row_ids:  # if there are rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(
                        criteria.row_ids):
                    if line.column in col_titles:
                        if line.value_adv_mat:
                            if criteria.column_value:
                                if line.value_adv_mat in criteria.column_value.split(','):
                                    result += int(line.value_adv_mat)
                            else:
                                result += int(line.value_adv_mat)
        else:  # all rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                    if line.column in col_titles:
                        if line.value_adv_mat:
                            if criteria.column_value:
                                if line.value_adv_mat in criteria.column_value.split(','):
                                    result += int(line.value_adv_mat)
                            else:
                                result += int(line.value_adv_mat)
        return result

    def calculate_type_count(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        if criteria.row_ids:  # if there are rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(
                        criteria.row_ids):
                    if line.column in col_titles:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += 1
        else:  # all rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                    if line.column in col_titles:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += 1
        return result

    def calculate_type_count_percentage(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        if criteria.row_ids:  # if there are rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(
                        criteria.row_ids):
                    if line.column in col_titles:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += 1
            result = float(result / len(criteria.row_ids)) * 100
        else:  # all rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                    if line.column in col_titles:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += 1
            nb_lines_all = 0
            for rec in criteria.question_ids:
                nb_lines = len(rec.labels_adv_matrix_rows_ids)
                nb_lines_all += nb_lines
            result = float(result / nb_lines_all) * 100
        return result

    def calculate_type_average(self, criteria, page, survey):
        sum = self.calculate_type_sum(criteria, page, survey)
        nb_lines = 0
        nb_lines_all = 0
        if criteria.row_ids:
            nb_lines_all = len(criteria.row_ids)
        else:
            for rec in criteria.question_ids:
                if rec.fill_auto:  # automatic fill
                    nb_lines = self.automatic_fill_lines(rec)
                if not rec.fill_auto:
                    nb_lines = len(rec.labels_adv_matrix_rows_ids)
                nb_lines_all += nb_lines
        if float(sum / nb_lines_all).is_integer():
            return int(sum / nb_lines_all)
        else:
            return float(sum / nb_lines_all)

    def calculate_type_sum_average_total(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        for line in self.user_input_line_ids:
            if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                if line.column in col_titles:
                    if line.value_adv_mat:
                        result += int(line.value_adv_mat)
        return result

    def calculate_type_average_total(self, criteria, page, survey):
        sum = self.calculate_type_sum(criteria, page, survey)
        if criteria.operation == 'average_total':
            denominator = self.calculate_type_sum_average_total(criteria, page, survey)
        if float(sum / denominator).is_integer():
            return int(sum / denominator)
        else:
            return float(sum / denominator)

    def calculate_type_sum_average_total_condition(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        for line in self.user_input_line_ids:
            if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                if line.column in col_titles:
                    if line.value_adv_mat:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += int(line.value_adv_mat)
        return result

    def calculate_type_average_total_condition(self, criteria, page, survey):
        sum = self.calculate_type_sum(criteria, page, survey)
        if criteria.operation == 'average_total_condition':
            denominator = self.calculate_type_sum_average_total_condition(criteria, page, survey)
        if float(sum / denominator).is_integer():
            return int(sum / denominator)
        else:
            return float(sum / denominator)

    def calculate_type_syntax(self, criteria, page, survey):
        code = criteria.code
        functions_list = ['VALUE','NB','REACTIVITY_DAT','REACTIVITY_EXPLOITATION','VALABS']
        code = self.replace_many(code,functions_list)
        exec(code)
        return locals()['result']

    def isfloat(self,value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def VALUE(self, page, question, column, row=None):
        if row:
            a_tag = '%s_%s_%s_%s_%s' % (self.survey_id.id, page, question, row, column)
            user_input_line_id = self.env['survey.user_input_line'].search([('user_input_id', '=', self.id), ('a_tag', '=', a_tag)],limit=1)
            value = user_input_line_id.value_adv_mat
            type_resp = user_input_line_id.type_resp
            if type_resp in ['number','float_number'] and value:
                value = float(value)

        else: #no rows in the begining case
            starting = '%s_%s_%s_' % (self.survey_id.id, page, question)
            ending = '_%s' % (column)
            sum_vals = 0
            for line in self.user_input_line_ids:
                if line.a_tag.startswith(starting) and line.a_tag.endswith(ending):
                    value = line.value_adv_mat
                    if line.type_resp in ['number', 'float_number'] and value:
                        value = float(value)
                        sum_vals += value
                    if line.type_resp in ['field_model'] and self.isfloat(value):
                        value = float(value)
                        sum_vals += value
            value = sum_vals
        return value

    def VALABS(self, page, question, column, row=None):
        if row:
            a_tag = '%s_%s_%s_%s_%s' % (self.survey_id.id, page, question, row, column)
            user_input_line_id = self.env['survey.user_input_line'].search([('user_input_id', '=', self.id), ('a_tag', '=', a_tag)],limit=1)
            value = user_input_line_id.value_adv_mat
            type_resp = user_input_line_id.type_resp
            if type_resp in ['number','float_number'] and value:
                value = abs(float(value))

        else: #no rows in the begining case
            starting = '%s_%s_%s_' % (self.survey_id.id, page, question)
            ending = '_%s' % (column)
            sum_vals = 0
            for line in self.user_input_line_ids:
                if line.a_tag.startswith(starting) and line.a_tag.endswith(ending):
                    value = line.value_adv_mat
                    if line.type_resp in ['number', 'float_number'] and value:
                        value = abs(float(value))
                        sum_vals += value
                    if line.type_resp in ['field_model'] and self.isfloat(value):
                        value = abs(float(value))
                        sum_vals += value
            value = sum_vals
        return value

    def replace_many(self,original_code, functions_list):
        # Traverse the functions list to replace
        for func in functions_list:
            # Test if string exists in the original string
            if func in original_code:
                # Replace the string
                original_code = original_code.replace(func, 'self.'+func)
        return original_code

    def NB(self, page, question, column, row=None):
        starting = '%s_%s_%s_' % (self.survey_id.id, page, question)
        if row:
            ending = '%s_%s' % (column,row)
        else:
            ending = '_%s' % (column)
        count = 0
        for line in self.user_input_line_ids:
            if line.a_tag.startswith(starting) and line.a_tag.endswith(ending):
                if line.value_adv_mat:
                    count += 1
        return count



    def calculate_type_count_total_condition_percentage(self, criteria, page, survey):
        result = 0
        count_notes = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        if criteria.row_ids:  # if there are rows
            for line in self.user_input_line_ids:
                if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(
                        criteria.row_ids):
                    if line.column in col_titles:
                        if line.value_adv_mat in criteria.column_value.split(','):
                            result += 1
        for line in self.user_input_line_ids:
            if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                if line.column in col_titles:
                    if line.value_adv_mat in criteria.column_value.split(','):
                        count_notes += 1

        return float(result/count_notes) * 100

    def calculate_type_average_denom_max_criteria(self, criteria, page, survey):
        sum = self.calculate_type_sum(criteria, page, survey)
        col_titles = []
        result = 0
        for col in criteria.column_ids:
            col_titles.append(col.value)
        for line in self.user_input_line_ids:
            if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                if line.column in col_titles:
                    if line.value_adv_mat or line.value_adv_mat == '0':
                        to_add = float(line.value_adv_mat) if float(line.value_adv_mat) > 1 else 1
                        result += to_add
                        to_add = 0
        return float(sum / result) * 100

    def old_session_reactivity_dat(self, current_session_info, site_id, page, criteria, note, note_values):
        result = -1
        count = 0
        count_current = 0
        lines_to_check = []
        old_survey_session_info_list = self.env['spc_survey.session.info'].search(['&', '&', ('survey_session_id', '=', current_session_info.survey_session_id.old_session_id.id),('site_id', '=', site_id.id), ('closing_date', '!=', False)])
        closing_date = old_survey_session_info_list[0].closing_date  # take the first date to compare with
        old_survey_session_info = old_survey_session_info_list[0]  # take the first old survey session info to compare with
        for survey_session_info in old_survey_session_info_list:
            if closing_date < survey_session_info.closing_date:
                closing_date = survey_session_info.closing_date
                old_survey_session_info = survey_session_info
        old_session_survey_user_input_list = self.env['survey.user_input'].search([('survey_session_info_id', '=', old_survey_session_info.id)])  # old detected
        for survey_user_input in old_session_survey_user_input_list:
            if survey_user_input.survey_id == self.survey_id.copied_from_id:
                old_survey_user_input = survey_user_input
                a_tags = []
                if not criteria.row_ids:  # if there are no rows
                    return 404
                else:
                    for line in old_survey_user_input.user_input_line_ids:
                        if line.page_id.id == self.env['survey.page'].search([('id', '=',page.id)]).duplicated_page and line.question_id.id in self.criteria_duplicated_questions(criteria) and int(line.a_tag.split('_')[3]) in self.criteria_duplicated_rows(criteria):
                            a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])

                    for line in old_survey_user_input.user_input_line_ids:
                        if line.page_id.id == self.env['survey.page'].search([('id', '=',page.id)]).duplicated_page and line.question_id.id in self.criteria_duplicated_questions(criteria) and int(line.a_tag.split('_')[3]) in self.criteria_duplicated_rows(criteria):
                            if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
                                if line.column == note and line.value_adv_mat in note_values.split(','):
                                    new_a_tag = str(self.survey_id.id) + '_' + str(page.id) + '_' + str(self.env['survey.question'].search([('survey_id', '=', self.survey_id.id), ('duplicated_question', '=', line.question_id.id)]).id) + '_' + str(self.env['survey.label'].search([('row_question_id', '=',self.env['survey.question'].search([('survey_id', '=', self.survey_id.id), ('duplicated_question', '=',line.question_id.id)]).id), ('duplicated_row', '=',int(line.a_tag.split('_')[3]))]).id)
                                    val = self.env['survey.user_input_line'].search(['&', '&', ('user_input_id', '=', self.id), ('a_tag', 'like', new_a_tag + '_'),('column', '=', note)])
                                    if val:
                                        lines_to_check.append(self.env['survey.user_input_line'].search([('user_input_id', '=', self.id), ('a_tag', '=', val.a_tag)]))
                                        count += 1
                break
        if count == 0: #all previous are conform
            return result
        if count > 0:
            #checking only previous session rows in current session
            for line in lines_to_check:
                if line.value_adv_mat not in note_values.split(','):
                    count_current += 1
        if count_current == 0: #rows not conform again :(
            return 0
        if count_current > 0: #there are some conform lines
            return count_current / count

    def REACTIVITY_DAT(self,criteria,page,note,note_values):
        criteria = self.env['spc_survey.scoring.criteria'].search([('id', '=', criteria)], limit=1)
        page = self.env['survey.page'].search([('id', '=', page)], limit=1)
        result = -1
        count = 0
        count_current = 0
        lines_to_check = []
        current_survey_session_info_id = self.survey_session_info_id
        site_id = current_survey_session_info_id.site_id
        opening_date = current_survey_session_info_id.opening_date
        survey_session_id = current_survey_session_info_id.survey_session_id
        # get M-1 Audit
        previous_survey_session_info_list = self.env['spc_survey.session.info'].search(['&', '&', ('survey_session_id', '=', survey_session_id.id), ('site_id', '=', site_id.id),'&', ('closing_date', '!=', False), ('closing_date', '<', opening_date)])  # all of them
        if not previous_survey_session_info_list:  # first time: (no previous)
            if survey_session_id.old_session_id:
                return self.old_session_reactivity_dat(current_survey_session_info_id,site_id,page,criteria,note,note_values)
            else:
                return result
        closing_date = previous_survey_session_info_list[0].closing_date  # take the first date to compare with
        previous_survey_session_info = previous_survey_session_info_list[0]  # take the first previous survey session info to compare with
        for survey_session_info in previous_survey_session_info_list:
            if closing_date < survey_session_info.closing_date:
                closing_date = survey_session_info.closing_date
                previous_survey_session_info = survey_session_info
        session_survey_user_input_list = self.env['survey.user_input'].search([('survey_session_info_id', '=', previous_survey_session_info.id)])  # previous detected
        for survey_user_input in session_survey_user_input_list:
            if survey_user_input.survey_id == self.survey_id:
                previous_survey_user_input = survey_user_input
                a_tags = []
                if not criteria.row_ids:  # if there are no rows
                    return 404
                else: #rows detected
                    for line in previous_survey_user_input.user_input_line_ids:
                        if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
                            a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])

                    for line in previous_survey_user_input.user_input_line_ids:
                        if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
                            if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
                                if line.column == note and line.value_adv_mat in note_values.split(','):
                                    lines_to_check.append(self.env['survey.user_input_line'].search([('user_input_id', '=', self.id), ('a_tag', '=', line.a_tag)]))
                                    count += 1
                break
        if count == 0: #all previous are conform
            return result
        if count > 0:
            #checking only previous session rows in current session
            for line in lines_to_check:
                if line.value_adv_mat not in note_values.split(','):
                    count_current += 1
        if count_current == 0: #rows not conform again :(
            return 0
        if count_current > 0: #there are some conform lines
            return count_current / count

    def criteria_duplicated_questions(self,criteria):
        questions = []
        for question in criteria.question_ids:
            questions.append(question.duplicated_question)
        return questions

    def criteria_duplicated_rows(self,criteria):
        rows = []
        for row in criteria.row_ids:
            rows.append(row.duplicated_row)
        return rows


    def old_session_reactivity_exploitation(self,current_session_info,site_id,page,criteria,direction_column,direction_value,note,note_values):
        result = -1
        count = 0
        count_current = 0
        lines_to_check = []
        old_survey_session_info_list = self.env['spc_survey.session.info'].search(['&', '&',('survey_session_id','=',current_session_info.survey_session_id.old_session_id.id),('site_id','=',site_id.id),('closing_date', '!=', False)])
        closing_date = old_survey_session_info_list[0].closing_date  # take the first date to compare with
        old_survey_session_info = old_survey_session_info_list[0] #take the first old survey session info to compare with
        for survey_session_info in old_survey_session_info_list:
            if closing_date < survey_session_info.closing_date:
                closing_date = survey_session_info.closing_date
                old_survey_session_info = survey_session_info
        old_session_survey_user_input_list = self.env['survey.user_input'].search([('survey_session_info_id', '=', old_survey_session_info.id)])  # old detected
        for survey_user_input in old_session_survey_user_input_list:
            if survey_user_input.survey_id == self.survey_id.copied_from_id:
                old_survey_user_input = survey_user_input
                a_tags = []
                for line in old_survey_user_input.user_input_line_ids:
                    if line.page_id.id == self.env['survey.page'].search([('id','=',page.id)]).duplicated_page and line.question_id.id in self.criteria_duplicated_questions(criteria):
                        if line.column == direction_column and line.value_adv_mat == direction_value:  # column name and #column value
                            a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])
                for line in old_survey_user_input.user_input_line_ids:
                    if line.page_id.id == self.env['survey.page'].search([('id','=',page.id)]).duplicated_page and line.question_id.id in self.criteria_duplicated_questions(criteria):
                        if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
                            if line.column == note and line.value_adv_mat in note_values.split(','):
                                new_a_tag = str(self.survey_id.id) + '_' +  str(page.id) + '_' + str(self.env['survey.question'].search([('survey_id','=',self.survey_id.id),('duplicated_question', '=', line.question_id.id)]).id) + '_' + str(self.env['survey.label'].search([('row_question_id', '=', self.env['survey.question'].search([('survey_id','=',self.survey_id.id),('duplicated_question', '=', line.question_id.id)]).id),('duplicated_row','=',int(line.a_tag.split('_')[3]))]).id)
                                val = self.env['survey.user_input_line'].search(['&', '&', ('user_input_id', '=', self.id), ('a_tag', 'like', new_a_tag + '_'), ('column', '=', note)])
                                if val:
                                    lines_to_check.append(self.env['survey.user_input_line'].search([('user_input_id', '=', self.id), ('a_tag', '=', val.a_tag)]))
                                    count += 1
                break
        if count == 0:  # all previous are conform
            return result
        if count > 0:
            # checking only previous session rows in current session
            for line in lines_to_check:
                if line.value_adv_mat not in note_values.split(','):
                    count_current += 1
        if count_current == 0:  # rows not conform again :(
            return 0
        if count_current > 0:  # there are some conform lines
            return count_current / count


    def REACTIVITY_EXPLOITATION(self,criteria,page,direction_column,direction_value,note,note_values):
        criteria = self.env['spc_survey.scoring.criteria'].search([('id', '=', criteria)], limit=1)
        page = self.env['survey.page'].search([('id', '=', page)], limit=1)
        result = -1
        count = 0
        count_current = 0
        lines_to_check = []
        current_survey_session_info_id = self.survey_session_info_id
        site_id = current_survey_session_info_id.site_id
        opening_date = current_survey_session_info_id.opening_date
        survey_session_id = current_survey_session_info_id.survey_session_id
        #get M-1 Audit
        previous_survey_session_info_list = self.env['spc_survey.session.info'].search(['&', '&',('survey_session_id','=',survey_session_id.id),('site_id','=',site_id.id),'&',('closing_date', '!=', False),('closing_date', '<', opening_date)]) #all of them
        if not previous_survey_session_info_list: #first time: (no previous)
            if survey_session_id.old_session_id:
                return self.old_session_reactivity_exploitation(current_survey_session_info_id,site_id,page,criteria,direction_column,direction_value,note,note_values)
            else:
                return result
        closing_date = previous_survey_session_info_list[0].closing_date #take the first date to compare with
        previous_survey_session_info = previous_survey_session_info_list[0] #take the first previous survey session info to compare with
        for survey_session_info in previous_survey_session_info_list:
            if closing_date < survey_session_info.closing_date:
                closing_date = survey_session_info.closing_date
                previous_survey_session_info = survey_session_info
        session_survey_user_input_list = self.env['survey.user_input'].search([('survey_session_info_id', '=', previous_survey_session_info.id)]) #previous detected
        for survey_user_input in session_survey_user_input_list:
            if survey_user_input.survey_id == self.survey_id:
                previous_survey_user_input = survey_user_input
                a_tags = []
                for line in previous_survey_user_input.user_input_line_ids:
                    if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                        if line.column == direction_column and line.value_adv_mat == direction_value: #column name and #column value
                            a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])

                for line in previous_survey_user_input.user_input_line_ids:
                    if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                        if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
                            if line.column == note and line.value_adv_mat in note_values.split(','):
                                lines_to_check.append(self.env['survey.user_input_line'].search([('user_input_id','=',self.id),('a_tag','=',line.a_tag)]))
                                count += 1
                break

        if count == 0: #all previous are conform
            return result
        if count > 0:
            #checking only previous session rows in current session
            for line in lines_to_check:
                if line.value_adv_mat not in note_values.split(','):
                    count_current += 1
        if count_current == 0: #rows not conform again :(
            return 0
        if count_current > 0: #there are some conform lines
            return count_current / count

    # def REACTIVITY(self,criteria,page,direction_column,direction_value,note,note_values,previous_audit):
    #     criteria = self.env['spc_survey.scoring.criteria'].search([('id','=',criteria)], limit=1)
    #     page = self.env['survey.page'].search([('id', '=', page)], limit=1)
    #     result = 0
    #     if previous_audit == 1:
    #         current_survey_session_info_id = self.survey_session_info_id
    #         site_id = current_survey_session_info_id.site_id
    #         survey_session_id = current_survey_session_info_id.survey_session_id
    #         #get M-1 Audit
    #         previous_survey_session_info_list = self.env['spc_survey.session.info'].search([('survey_session_id','=',survey_session_id.id),('site_id','=',site_id.id)])
    #         closing_date = previous_survey_session_info_list[0].closing_date
    #         previous_survey_session_info = previous_survey_session_info_list[0]
    #         for survey_session_info in previous_survey_session_info_list:
    #             if survey_session_info == current_survey_session_info_id:
    #                 break
    #             if closing_date < survey_session_info.closing_date:
    #                 closing_date = survey_session_info.closing_date
    #                 previous_survey_session_info = survey_session_info
    #         #check if first time:
    #         if survey_session_info == previous_survey_session_info_list[0]:
    #             return 1
    #         #####################
    #         session_survey_user_input_list = self.env['survey.user_input'].search([('survey_session_info_id','=',previous_survey_session_info.id)])
    #
    #         for survey_user_input in session_survey_user_input_list:
    #             if survey_user_input.survey_id == self.survey_id:
    #                 previous_survey_user_input = survey_user_input
    #
    #
    #                 a_tags = []
    #                 if criteria.row_ids:  # if there are rows
    #                     for line in previous_survey_user_input.user_input_line_ids:
    #                         if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
    #                             if line.column == direction_column:
    #                                 if line.value_adv_mat == direction_value:
    #                                     a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])
    #
    #                     for line in previous_survey_user_input.user_input_line_ids:
    #                         if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
    #                             if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
    #                                 if line.column == note:
    #                                     if line.value_adv_mat in note_values.split(','):
    #                                         result += 1
    #                 else:
    #                     for line in previous_survey_user_input.user_input_line_ids:
    #                         if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
    #                             if line.column == direction_column:
    #                                 if line.value_adv_mat == direction_value:
    #                                     a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])
    #
    #                     for line in previous_survey_user_input.user_input_line_ids:
    #                         if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
    #                             if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
    #                                 if line.column == note:
    #                                     if line.value_adv_mat in note_values.split(','):
    #                                         result += 1
    #                 break
    #
    #
    #
    #         return result
    #
    #     else: #current_audit
    #         a_tags = []
    #         if criteria.row_ids:  # if there are rows
    #             for line in self.user_input_line_ids:
    #                 if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
    #                     if line.column == direction_column:
    #                         if line.value_adv_mat == direction_value:
    #                             a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])
    #             for line in self.user_input_line_ids:
    #                 if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids and line.row in self.check_row(criteria.row_ids):
    #                     if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
    #                         if line.column == note:
    #                             if line.value_adv_mat in note_values.split(','):
    #                                 result += 1
    #         else:  # all rows
    #             for line in self.user_input_line_ids:
    #                 if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
    #                     if line.column == direction_column:
    #                         if line.value_adv_mat == direction_value:
    #                             a_tags.append(line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3])
    #             for line in self.user_input_line_ids:
    #                 if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
    #                     if line.a_tag.split('_')[0] + '_' + line.a_tag.split('_')[1] + '_' + line.a_tag.split('_')[2] + '_' + line.a_tag.split('_')[3] in a_tags:
    #                         if line.column == note:
    #                             if line.value_adv_mat in note_values.split(','):
    #                                 result += 1
    #     return result


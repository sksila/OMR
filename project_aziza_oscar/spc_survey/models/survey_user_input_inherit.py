import logging

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug,unslug


class SurveyUserInputInherit(models.Model):
    _inherit = "survey.user_input"
    # _inherit = ['survey.user_input', 'mail.thread', 'mail.activity.mixin']

    survey_session_info_id = fields.Many2one('spc_survey.session.info', readonly=True)
    criteria_ids = fields.One2many('spc_survey.user_input_criteria','user_input_id', string="Critéres")
    final_score = fields.Float('Final Score', compute="calculate_final_score", store=True)
    final_score_char = fields.Char('Final Score', compute="calculate_final_score", store=True)

    # simple view answers via web
    @api.multi
    def action_view_answers(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "View Answers",
            'target': 'self',
            'url': '%s/%s/%s' % (self.print_url, self.token, 'view_answers')
        }


    def calculate_scores(self):
        final_score_criteria = []
        for page in self.survey_id.page_ids:
            for crit in self.env['spc_survey.scoring'].search([('page_id','=',page.id)]).final_score_criteria:
                final_score_criteria.append(crit.id)
            if self.env['spc_survey.scoring'].search([('page_id','=',page.id)]).scoring_criteria_ids:
                for criteria in self.env['spc_survey.scoring'].search([('page_id','=',page.id)]).scoring_criteria_ids:
                    try:
                        scorer = getattr(self, 'calculate_type_' + str(criteria.operation))
                    except AttributeError:
                        logging.error("No scoring function for this criteria")
                        return False
                    else:
                        result = scorer(criteria,page,page.survey_id)
                        if len(self.criteria_ids) != len(self.env['spc_survey.scoring'].search([('page_id','=',page.id)]).scoring_criteria_ids):
                            if criteria.operation in ['percentage']:
                                self.write({
                                    'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id':page.id, 'is_final':criteria.id in final_score_criteria,
                                                        'score_float': round(result), 'score_text': str(round(result)) + '%', 'criteria_id':criteria.id,
                                                        'coefficient':criteria.coefficient})]
                                })
                            else:
                                self.write({
                                    'criteria_ids': [(0, 0, {'name': criteria.criteria_name, 'page_id':page.id, 'is_final':criteria.id in final_score_criteria,
                                                             'score_float': result, 'score_text': str(round(result)), 'criteria_id':criteria.id,
                                                             'coefficient':criteria.coefficient})]
                                })


    def calculate_type_sum(self, criteria, page, survey):
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

    def calculate_type_count(self, criteria, page, survey):
        result = 0
        col_titles = []
        for col in criteria.column_ids:
            col_titles.append(col.value)
        for line in self.user_input_line_ids:
            if line.page_id.id == page.id and line.question_id.id in criteria.question_ids.ids:
                if line.column in col_titles:
                    # if line.value_adv_mat == criteria.column_value:
                    if line.value_adv_mat in criteria.column_value.split(','):
                        result += 1
        return result

    def calculate_type_average(self, criteria, page, survey):
        sum = self.calculate_type_sum(criteria, page, survey)
        nb_lines = 0
        nb_lines_all = 0
        for rec in criteria.question_ids:
            if rec.fill_auto: #automatic fill
                nb_lines = self.automatic_fill_lines(rec)
            if not rec.fill_auto:
                nb_lines = len(rec.labels_adv_matrix_rows_ids)
            nb_lines_all += nb_lines
        if float(sum/nb_lines_all).is_integer():
            return int(sum/nb_lines_all)
        else:
            return float(sum / nb_lines_all)

    def calculate_type_percentage(self, criteria, page, survey):
        return self.calculate_type_average(criteria, page, survey) * 100

    def automatic_fill_lines(self,question):
        max = 0
        for line in self.user_input_line_ids:
            if line.question_id.id == question.id:
                if max<int(line.row):
                    max = int(line.row)
        return max+1

    @api.depends('criteria_ids')
    @api.one
    def calculate_final_score(self):
        scores = []
        sum = 0
        denom = 0
        for crit in self.criteria_ids:
            if crit.is_final:
                scores.append((crit.score_float,crit.coefficient))
        if scores:
            for rec in scores:
                sum += rec[0] * rec[1]
                denom += rec[1]
            if float(sum/denom).is_integer():
                self.final_score = int(float(sum/denom))
            else:
                self.final_score = round(float(sum/denom))
            self.final_score_char = str(self.final_score) + '%'






class SurveyUserInputCriteria(models.Model):
    _name = "spc_survey.user_input_criteria"
    _description = "Scoring de réponse du maquette"

    name = fields.Char('Title')
    score_text = fields.Char('Result')
    score_float = fields.Float('Result', digits=(6,2))
    display_type = fields.Selection([
        ('line_section', "Section")], default=False, help="Technical field for UX purpose.")
    page_id = fields.Many2one('survey.page')
    is_final = fields.Boolean(default=False)
    criteria_id = fields.Many2one('spc_survey.scoring.criteria')
    coefficient = fields.Float('coefficient', default=1)
    user_input_id = fields.Many2one('survey.user_input')












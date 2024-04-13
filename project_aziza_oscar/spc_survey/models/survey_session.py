import logging
import re
from odoo import fields, models, api, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class SpcSurveySessionInfo(models.Model):
    _name = "spc_survey.session.info"
    _description = "Informations du session d'audit "
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True)
    opening_date = fields.Datetime(string="Opening date")
    closing_date = fields.Datetime(string="Closing date")
    site_id = fields.Many2one('oscar.site', string='Site')
    auditor_id = fields.Many2one('res.users', string='Auditor')
    activity_id = fields.Many2one('mail.activity')
    session_final_score = fields.Float('Session final score', group_operator=False)
    survey_session_id = fields.Many2one(comodel_name='spc_survey.session', string="survey session")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.ref('base.main_company').id)
    is_test_session = fields.Boolean('Is Test Session', default=False)
    rank = fields.Char('Rang', compute='compute_rank', store=True)
    group_ids = fields.Char(compute="_compute_group_ids",search='group_ids_search')

    @api.one
    def _compute_group_ids(self):
        pass

    def group_ids_search(self, operator, operand):
        groups = [g.id for g in self.env.user.groups_id]
        return [('survey_session_id.survey_type_id.group_ids', 'in', groups)]


    def session_scoring_line_scoring(self,session_scoring_line):
        survey_ids = session_scoring_line.survey_ids
        page_ids = session_scoring_line.page_ids
        criteria_ids = session_scoring_line.scoring_criteria_ids
        operation = session_scoring_line.operation
        if operation:
            if criteria_ids:
                if len(criteria_ids) == 1: #operation and one criteria
                    raise ValidationError(_("Choose one more criteria!"))
                else: #operation and more than one criteria
                    try:
                        scorer = getattr(self, 'final_report_operation_' + str(operation))
                    except AttributeError:
                        logging.error("No function for this criteria")
                        return False
                    else:
                        result = scorer(criteria_ids)
                        return result
            else: #no criteria
                if page_ids:
                    if len(page_ids) == 1: #operation and no criteria and one page
                        raise ValidationError(_("Choose one more page!"))
                    else: #operation and no criteria and more than pages
                        try:
                            scorer = getattr(self, 'final_report_operation_' + str(operation))
                        except AttributeError:
                            logging.error("No function for those pages")
                            return False
                        else:
                            result = scorer(page_ids)
                            return result
                else:  # no pages
                    if survey_ids:
                        if len(survey_ids) == 1:
                            raise ValidationError(_("Choose one more survey!"))
                        else:  # operation and no criteria and no pages and more than survey
                            try:
                                scorer = getattr(self, 'final_report_operation_' + str(operation))
                            except AttributeError:
                                logging.error("No function for those surveys")
                                return False
                            else:
                                result = scorer(survey_ids)
                                return result
                    else:
                        return ''
        else: #no operation
            if criteria_ids:
                if len(criteria_ids) == 1:
                    return self.criteria_score(criteria_ids[0])
                else:
                    raise ValidationError(_("Choose an operation!"))
            else: #no criteria
                if page_ids:
                    if len(page_ids) == 1:
                        return self.final_page_score(page_ids[0])
                    else:
                        raise ValidationError(_("Choose an operation!"))
                else: #no pages
                    if survey_ids:
                        if len(survey_ids) == 1:
                            return self.final_survey_score(survey_ids[0])
                        else:
                            raise ValidationError(_("Choose an operation!"))
                    else:
                        return ''

    def final_survey_score(self,survey):#maquette
        return str(round(float(self.env['survey.user_input'].search([('survey_id','=',survey.id),('survey_session_info_id','=',self.id)], limit=1).final_score))) + '%'

    def final_page_score(self,page): #page , il faut la calculer puisq c pas persisté
        if len(page.survey_id.page_ids) == 1:
            return str(round(float(self.env['survey.user_input'].search([('survey_id','=',page.survey_id.id),('survey_session_info_id','=',self.id)]).final_score_char.replace('%','')))) + '%'
        else:
            user_input_id = self.env['survey.user_input'].search([('survey_id','=',page.survey_id.id),('survey_session_info_id','=',self.id)])
            scores=[]
            coeffs=[]
            for rec in user_input_id.criteria_ids:
                if rec.page_id.id == page.id:
                    scores.append(rec.score_float*rec.coefficient)
                    coeffs.append(rec.coefficient)
            return str(round(float(sum(scores)/sum(coeffs)))) + '%'

    def criteria_score(self,criteria):
        criteria_list = self.env['survey.user_input'].search([('survey_id','=',criteria.survey_id.id),('survey_session_info_id','=',self.id)], limit=1).criteria_ids
        for line in criteria_list:
            if line.criteria_id.id == criteria.id:
                return line.score_text
        return ''

    def final_report_operation_sum(self,criteria_or_page_or_survey):
        if 'survey.survey' in str(type(criteria_or_page_or_survey)):
            list_surveys = []
            for survey in criteria_or_page:
                list_surveys.append(round(float(self.final_survey_score(survey).replace('%',''))))
            return sum(list_surveys)
        elif 'survey.page' in str(type(criteria_or_page_or_survey)):
            list_pages = []
            for page in criteria_or_page_or_survey:
                list_pages.append(round(float(self.final_page_score(page).replace('%',''))))
            return sum(list_pages)
        else: #criteria
            list_criteria = []
            for criteria in criteria_or_page_or_survey:
                list_criteria.append(round(float(re.sub('[^0-9.]+', '', self.criteria_score(criteria)))))
            return sum(list_criteria)


    def final_report_operation_count(self,criteria_or_page_or_survey):
        if 'survey.survey' in str(type(criteria_or_page_or_survey)):
            survey_count = 0
            for survey in criteria_or_page_or_survey:
                survey_count += 1
            return survey_count
        elif 'survey.page' in str(type(criteria_or_page_or_survey)):
            pages_count = 0
            for page in criteria_or_page_or_survey:
                pages_count += 1
            return pages_count
        else:
            criteria_count = 0
            for criteria in criteria_or_page_or_survey:
                criteria_count += 1
            return criteria_count


    def final_report_operation_average(self,criteria_or_page_or_survey):
        if 'survey.survey' in str(type(criteria_or_page_or_survey)):
            list_surveys = []
            count_survey = 0
            for survey in criteria_or_page_or_survey:
                list_surveys.append(round(float(self.final_survey_score(survey).replace('%',''))))
                count_survey += 1
            return round(float(sum(list_surveys) / count_survey))
        elif 'survey.page' in str(type(criteria_or_page_or_survey)):
            list_pages = []
            count_page = 0
            for page in criteria_or_page_or_survey:
                list_pages.append(round(float(self.final_page_score(page).replace('%',''))))
                count_page += 1
            return round(float(sum(list_pages) / count_page))
        else:
            list_criteria = []
            count_criteria = 0
            for criteria in criteria_or_page_or_survey:
                list_criteria.append(round(float(re.sub('[^0-9.]+', '', self.criteria_score(criteria)))))
                count_criteria += 1
            return round(float(sum(list_criteria) / count_criteria))


    def final_report_operation_percentage(self,criteria_or_page_or_survey):
        if 'survey.survey' in str(type(criteria_or_page_or_survey)):
            return str(self.final_report_operation_average(criteria_or_page_or_survey)) + '%'
        elif 'survey.page' in str(type(criteria_or_page_or_survey)):
            return str(self.final_report_operation_average(criteria_or_page_or_survey)) + '%'
        else:
            return str(self.final_report_operation_average(criteria_or_page_or_survey)) + '%'

    def session_final_scoring(self,criterias,session):
        list = []
        float_list = []
        count = 0
        for criteria in criterias:
            list.append(self.session_scoring_line_scoring(criteria))
            count += 1
        for item in list:
            float_list.append(round(float(re.sub('[^0-9.]+', '', item))))
        if not session.session_final_score:
            session.sudo().write({
                'session_final_score' : round(float(sum(float_list) / count))
            })
        return round(float(sum(float_list) / count))

    def get_emails_list(self):
        email_ids = ''
        for user in self.survey_session_id.send_to_users_ids:
            email_ids = email_ids + ',' + str(user.partner_id.email)
        return email_ids

    @api.one
    @api.depends('survey_session_id', 'site_id','closing_date')
    def compute_rank(self):
        count = 0
        current_year = datetime.now().year
        for rec in self.env['spc_survey.session.info'].search(['&','&',('survey_session_id','=',self.survey_session_id.id),('site_id','=',self.site_id.id),('closing_date', '!=', False)]):
            if rec.closing_date and rec.closing_date.date().year == current_year:
                count +=1
        if count > 0:
            self.rank = '%s/%s' % (str(count),str(current_year))
        else:
            self.rank = ''

class SpcSurveySession(models.Model):
    _name = 'spc_survey.session'
    _description = "Session d'audit (série de maquettes)"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, track_visibility='onchange')
    survey_ids = fields.Many2many(comodel_name='survey.survey', column1='survey_session_id', column2='survey_id',
                                  relation='rel_survey_session_survey')
    description = fields.Text(string='Description')
    survey_type_id = fields.Many2one(comodel_name='spc_survey.type', string='Survey type')
    active = fields.Boolean(string="Active", default=True, track_visibility='onchange')
    session_scoring_ids = fields.One2many('spc_survey.session_scoring','session_scoring_id', string="Session scoring")
    session_final_score_title = fields.Char('Title', readonly=True)
    session_final_score_criteria = fields.Many2many('spc_survey.session_scoring', 'rel_session_final_score_criteria',
                                            string="Final score session Criteria", readonly=True)
    send_to_users_ids = fields.Many2many('res.users',string="Send final report to :")
    anomalies_report_ids = fields.One2many('spc_survey.anomalies.report','survey_session_id', string="Anomalies report")
    state = fields.Selection([('draft','Brouillon'),('validated','Validée')], string="Etat", default="draft")
    task_count = fields.Integer(compute='compute_count')
    old_session_id = fields.Many2one('spc_survey.session', string="Session ancienne")


    def get_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tâches',
            'view_mode': 'tree',
            'res_model': 'mail.activity',
            'domain': [('res_name', '=', self.name)],
            'context': "{'create': False}"
        }

    def compute_count(self):
        for record in self:

            record.task_count = self.env['mail.activity'].search_count([('res_name', '=', record.name)])

    @api.multi
    def toggle_active(self):
        if self.active:
            self.write({'active': False})
        else:
            self.write({'active': True})

    # @api.multi
    # def start_survey_session(self):
    #     self.ensure_one()
    #     url = self.survey_ids[0].public_url
    #     # create survey session info:
    #     survey_session_info_id = self.env['spc_survey.session.info'].sudo().create({
    #         'opening_date': fields.Datetime.now(),
    #         'name': self.name,
    #         'survey_session_id': self.id,
    #         #'site_id' : ,
    #         #'auditor_id' :
    #     })
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'name': "Launch survey session",
    #         'target': 'self',
    #         'url': str(self.survey_ids[0].with_context(relative_url=True).public_url) + "/" + str(slug(survey_session_info_id))
    #     }

    @api.multi
    def start_test_survey_session(self):
        self.ensure_one()
        url = self.survey_ids[0].public_url
        # create survey session info:
        survey_session_info_id = self.env['spc_survey.session.info'].sudo().create({
            'opening_date': fields.Datetime.now(),
            'name': self.name,
            'survey_session_id': self.id,
            'is_test_session' : True
        })
        return {
            'type': 'ir.actions.act_url',
            'name': "Launch survey session",
            'target': 'self',
            'url': str(self.survey_ids[0].with_context(relative_url=True).public_url) + "/" + str(slug(survey_session_info_id))
        }

    def validate_session(self):
        for survey in self.survey_ids:
            if survey.stage_id != self.env.ref('survey.stage_permanent'):
                raise UserError(_("La maquette %s n'est pas validée" %(survey.title)))
        self.write({'state' : 'validated'})

    def back_draft_session(self):
        self.write({'state': 'draft'})

class SpcSurveySessionScoring(models.Model):
    _name = "spc_survey.session_scoring"

    name = fields.Char(string="name")
    sequence = fields.Integer('seq number', default=10)
    scoring_criteria_ids = fields.Many2many('spc_survey.scoring.criteria', 'rel_scoring_session_scoring_criteria',string="Criteria")
    page_ids = fields.Many2many('survey.page','rel_page_session_scoring', string="Pages")
    operation = fields.Selection(
        [('sum', 'sum'), ('count', 'count'), ('average', 'average'), ('percentage', 'percentage')],
        string="Operation")
    session_scoring_id = fields.Many2one('spc_survey.session')
    domain_scoring_criteria_ids = fields.Many2many('spc_survey.scoring.criteria', 'relation_domain_scoring_criteria_ids',
                                                   compute="get_domain_scoring_criteria_ids")
    survey_ids = fields.Many2many('survey.survey','rel_scoring_session_scoring_survey_ids', string='Maquettes')
    domain_pages_ids = fields.Many2many('survey.page', 'rel_scoring_session_scoring_domain_pages_ids', compute="get_domain_pages_ids")

    @api.depends('survey_ids')
    @api.one
    def get_domain_pages_ids(self):
        page_list = []
        if self.survey_ids:
            for survey in self.survey_ids:
                for page in survey.page_ids:
                    page_list.append(page.id)
        self.domain_pages_ids = [(6, 0, page_list)]

    @api.depends('page_ids')
    @api.one
    def get_domain_scoring_criteria_ids(self):
        criteria_list = []
        if self.page_ids:
            for page in self.page_ids:
                if self.env['spc_survey.scoring'].search([('page_id', '=', page.id)]):
                        for criteria in self.env['spc_survey.scoring'].search([('page_id', '=', page.id)], limit=1).scoring_criteria_ids:
                            criteria_list.append(criteria.id)
        self.domain_scoring_criteria_ids = [(6, 0, criteria_list)]

class SpcSurveyAnomaliesReport(models.Model):
    _name = "spc_survey.anomalies.report"

    survey_id = fields.Many2one('survey.survey', string="Survey", required=True)
    page_id = fields.Many2one('survey.page', string="Page", required=True)
    question_id = fields.Many2one('survey.question', string="Question", required=True)
    row_ids = fields.Many2many('survey.label', string="Rows")
    column_id = fields.Many2one('survey.label', string="Column", required=True)
    column_value = fields.Char('Value')
    survey_session_id = fields.Many2one('spc_survey.session')

    @api.onchange('survey_id')
    def _onchange_survey_id(self):
        page_ids = self.survey_id.page_ids.ids
        return {'domain': {'page_id': [('id', 'in', page_ids)]}}

    @api.onchange('page_id')
    def _onchange_page_id(self):
        question_ids = self.page_id.question_ids.ids
        return {'domain': {'question_id': [('id', 'in', question_ids)]}}

    @api.onchange('question_id')
    def _onchange_question_id(self):
        column_ids = self.question_id.labels_adv_matrix_cols_ids.ids
        return {'domain': {'column_id': [('id', 'in', column_ids)]} }

    @api.onchange('question_id')
    def _onchange_row_ids(self):
        rows = self.question_id.labels_adv_matrix_rows_ids.ids
        return {'domain': {'row_ids': [('id', 'in', rows)]}}
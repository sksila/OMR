import json
import logging
from datetime import datetime
from odoo import fields, http
from odoo.http import request
from odoo.addons.spc_survey.controllers.main import SurveyControllerInherit

_logger = logging.getLogger(__name__)
from odoo.addons.http_routing.models.ir_http import slug,unslug


class SurveyExtraControllerInherit(SurveyControllerInherit):

    @http.route(['/survey/prefill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/prefill/<model("survey.survey"):survey>/<string:token>/<model("survey.page"):page>'],
                type='http', auth='public', website=True)
    def prefill(self, survey, token, page=None, **post):
        UserInputLine = request.env['survey.user_input_line']
        ret = {}
        # Fetch previous answers
        if page:
            previous_answers = UserInputLine.sudo().search([('user_input_id.token', '=', token), ('page_id', '=', page.id)])
        else:
            previous_answers = UserInputLine.sudo().search([('user_input_id.token', '=', token)])

        # Return non empty answers in a JSON compatible format
        for answer in previous_answers:
            if not answer.skipped:
                answer_tag = '%s_%s_%s' % (answer.survey_id.id, answer.page_id.id, answer.question_id.id)
                answer_value = None
                if answer.answer_type == 'free_text':
                    answer_value = answer.value_free_text
                elif answer.answer_type == 'text' and answer.question_id.type == 'textbox':
                    answer_value = answer.value_text
                elif answer.answer_type == 'text' and answer.question_id.type != 'textbox':
                    # here come comment answers for matrices, simple choice and multiple choice
                    answer_tag = "%s_%s" % (answer_tag, 'comment')
                    answer_value = answer.value_text
                elif answer.answer_type == 'number':
                    answer_value = str(answer.value_number)
                elif answer.answer_type == 'date':
                    answer_value = fields.Date.to_string(answer.value_date)
                elif answer.answer_type == 'suggestion' and not answer.value_suggested_row:
                    answer_value = answer.value_suggested.id
                elif answer.answer_type == 'suggestion' and answer.value_suggested_row:
                    answer_tag = "%s_%s" % (answer_tag, answer.value_suggested_row.id)
                    answer_value = answer.value_suggested.id

                #my advanced matrix c0d3
                elif answer.answer_type == 'adv_mat':
                    answer_tag = answer.a_tag
                    if answer.type_resp in ['text','textarea','number','float_number','date','dropdown','cam','model','field_model']: #add model type_resp
                        answer_value = answer.value_adv_mat
                    elif answer.type_resp == 'attachment':
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', default='')
                        base_url_attachment = base_url + '/web/content/'
                        attachments_list = []
                        for attach in answer.value_adv_mat_attachment:
                            attachments_list.append([attach.name,base_url_attachment + str(attach.id)])
                        answer_value = attachments_list
                #end.

                if answer_value:
                    ret.setdefault(answer_tag, []).append(answer_value)
                else:
                    # _logger.warning("[survey] No answer has been found for question %s marked as non skipped" % answer_tag)
                    pass
        return json.dumps(ret, default=str)

    def update_model(self,line,new_value):
        line.write({
            'value_adv_mat_model': new_value,
            'value_adv_mat': new_value,
        })

    def update_field_model(self,line,new_value):
        pass


    # correction table
    @http.route('/survey/<model("spc_survey.session.info"):survey_session_info>/correction', type='http', auth="public", website=True)
    def correction(self,survey_session_info, **post):
        data = ({
            'survey_session_info' : survey_session_info,
            })
        return request.render("spc_survey_extra.correction", data)

    # Printing correction routes
    @http.route(['/survey/print/<model("survey.survey"):survey>',
                '/survey/print/<model("survey.survey"):survey>/<string:token>',
                '/survey/print/<model("survey.survey"):survey>/<string:token>/<model("spc_survey.session.info"):survey_session_info>/correction'],
                type='http', auth='public', website=True, sitemap=False)
    def print_survey(self, survey, survey_session_info=None, token=None, **post):
        '''Display an survey in printable view; if <token> is set, it will
        grab the answers of the user_input_id that has <token>.'''
        if '/correction' in request.httprequest.url:
            return self._print_survey(survey, token, survey_session_info)
        else:
            return self._print_survey(survey, token)

    def _print_survey(self, survey, token=None, survey_session_info=None):
        return request.render(
                'survey.survey_print', {
                    'survey': survey,
                    'token': token,
                    'page_nr': 0,
                    'quizz_correction': True if survey.quizz_mode and token else False,
                    'survey_session_info':survey_session_info
                }
            )

    # survey/edit
    @http.route(['/survey/edit/<model("survey.survey"):survey>/<string:token>',
                 '/survey/edit/<model("survey.survey"):survey>/<string:token>/<model("spc_survey.session.info"):survey_session_info>/correction'], type='http', auth="public", website=True)
    def edit_response(self, survey, token,survey_session_info=None, **post):
        vals = ({
            'edit': True,
            'token': token,
            'survey': survey,
            'survey_session_info': survey_session_info
                })
        return request.render("survey.survey_print", vals)

    # survey/save
    @http.route(['/survey/save/<model("survey.survey"):survey>/<string:token>/correction',
                 '/survey/save/<model("survey.survey"):survey>/<string:token>'], type='http', auth="public", website=True)
    def save_response(self, survey, token, **post):
        ret = {}
        UserInput = request.env['survey.user_input']
        user_input = UserInput.sudo().search([('token', '=', token)], limit=1)

        #get questions
        questions = []
        for page in user_input.survey_id.page_ids:
            for question in page.question_ids:
                questions.append([question,str(user_input.survey_id.id) + '_' + str(page.id) + '_' + str(question.id)])
        # Answer validation
        errors = {}
        for question in questions:
            # answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
            errors.update(question[0].validate_question(post, question[1]))
        ret = {}
        if len(errors):
            # Return errors messages to webpage
            ret['errors'] = errors
            return json.dumps(ret)

        for line in user_input.user_input_line_ids:
            for key in post:
                if line.a_tag == key and line.value_adv_mat != post[key]:
                    try:
                        updater = getattr(self, 'update_' + line.type_resp)
                    except AttributeError:
                        _logger.warning(line.type_resp + ": This type of question has no save method")
                        return {}
                    else:
                        updater(line, post[key])
        ret['redirect'] = '/survey/fill/%s/%s' % (slug(survey), token)
        if 'correction' in post.keys():
            if 'survey_session_info' in post.keys():
                survey_session_info = str(slug(request.env['spc_survey.session.info'].search([('id','=',int(post['survey_session_info']))])))
                ret['redirect'] = '/survey/%s/correction' % (survey_session_info)
                user_input.sudo().write({'is_correction_done' : True})
        return json.dumps(ret)

    # scoring
    @http.route(['/survey/scoring/<model("spc_survey.session.info"):survey_session_info>/correction',
                 '/survey/scoring/<model("survey.survey"):survey>/<string:token>'], type='http', auth="public", website=True)
    def scoring(self, survey=None, token=None, survey_session_info=None, **post):
        #get pages of this session
        if survey_session_info:
            list = []
            for rec in request.env['survey.user_input'].search([('survey_session_info_id','=',survey_session_info.id)]):
                list.append(rec)
                rec.calculate_scores()
            survey_session_info.sudo().write({
                'closing_date': datetime.today()
            })
            vals = ({
                'survey_session_info': survey_session_info
                })
            return request.render("spc_survey_extra.session_scores",vals)
        else:
            request.env['survey.user_input'].search([('token', '=', token)]).calculate_scores()
            vals = ({
                'token': token
            })
            return request.render("spc_survey.single_survey_scores",vals)

    # /survey/session_scores/
    @http.route('/survey/session_scores/<model("spc_survey.session.info"):survey_session_info>', type='http',
                    auth="public", website=True)
    def session_scores(self, survey_session_info, **kwargs):
        pass

    # /survey/end_session/
    @http.route(['/survey/end_session/<model("spc_survey.session.info"):survey_session_info>',
                 '/survey/end_session/<string:token>'], type='http', auth="public", website=True)
    def session_scores(self, token=None, survey_session_info=None, **kwargs):
        menu_id = request.env.ref('survey.menu_surveys').id
        if survey_session_info:
            #calculate session score
            if survey_session_info.survey_session_id.session_final_score_criteria:
                survey_session_info.session_final_scoring(survey_session_info.survey_session_id.session_final_score_criteria,survey_session_info)
            #send final report
            if survey_session_info.survey_session_id.send_to_users_ids:
                final_report_template = request.env.ref('spc_survey.spc_survey_template_final_report')
                request.env['mail.template'].browse(final_report_template.id).send_mail(survey_session_info.id, force_send=True)
            #return to Odoo backend session info view
            action_id = request.env.ref('spc_survey.action_spc_survey_session_information').id
            active_id = survey_session_info.survey_session_id.id
            request.env['mail.activity'].search([('id','=',survey_session_info.activity_id.id)]).write({'workflow_activity' : 'done'})
            return request.redirect('/web#id=%s&action=%s&active_id=%s&model=spc_survey.session.info&view_type=form&menu_id=%s' % (str(survey_session_info.id),str(action_id),str(active_id),str(menu_id)))
        else:
            action_id = request.env.ref('survey.action_survey_user_input').id
            resp_id = request.env['survey.user_input'].search([('token', '=', token)]).id
            return request.redirect('/web#id=%s&action=%s&model=survey.user_input&view_type=form&menu_id=%s' % (str(resp_id),str(action_id),str(menu_id)))






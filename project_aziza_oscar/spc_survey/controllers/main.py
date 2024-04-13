import json
import logging
import base64
import werkzeug
from datetime import datetime
from math import ceil
from odoo import fields, http, _, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr
_logger = logging.getLogger(__name__)
from odoo.addons.survey.controllers.main import Survey
from odoo.addons.http_routing.models.ir_http import slug,unslug


class SurveyControllerInherit(Survey):



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

                #advanced matrix c0d3
                elif answer.answer_type == 'adv_mat':
                    answer_tag = answer.a_tag
                    if answer.type_resp in ['text','textarea','number','float_number','date','dropdown','cam']:
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

    # survey/edit
    @http.route(['/survey/edit/<model("survey.survey"):survey>/<string:token>'], type='http', auth="public", website=True)
    def edit_response(self, survey, token, **post):
        vals = ({
            'edit': True,
            'token': token,
            'survey': survey,
                })
        return request.render("survey.survey_print", vals)

    # survey/save
    @http.route(['/survey/save/<model("survey.survey"):survey>/<string:token>'], type='http', auth="public", website=True)
    def save_response(self, survey, token, **post):
        ret = {}
        UserInput = request.env['survey.user_input']
        user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
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
        return json.dumps(ret)

    def update_text(self,line,new_value):
        line.write({
            'value_adv_mat_text': new_value,
            'value_adv_mat': new_value,
        })

    def update_textarea(self,line,new_value):
        line.write({
            'value_adv_mat_textarea': new_value,
            'value_adv_mat': new_value,
        })

    def update_number(self,line,new_value):
        if new_value:
            line.write({
                'value_adv_mat_number': int(new_value),
                'value_adv_mat': new_value,
            })
        if not new_value:
            line.write({
                'value_adv_mat_number': int(0),
                'value_adv_mat': new_value,
            })

    def update_float_number(self,line,new_value):
        if new_value:
            line.write({
                'value_adv_mat_float_number': float(new_value),
                'value_adv_mat': new_value,
            })
        if not new_value:
            line.write({
                'value_adv_mat_float_number': float(0),
                'value_adv_mat': new_value,
            })

    def update_date(self,line,new_value):
        if new_value:
            line.write({
                'value_adv_mat_date': new_value,
                'value_adv_mat': new_value,
            })
        if not new_value:
            line.write({
                'value_adv_mat_float_number': False,
                'value_adv_mat': False,
            })

    def update_dropdown(self,line,new_value):
        line.write({
            'value_adv_mat_dropdown': new_value,
            'value_adv_mat': new_value,
        })

    def update_cam(self,line,new_value):
        #unlink old photo attachment
        request.env['ir.attachment'].search([('id', '=', int(line.value_adv_mat_cam.id))]).sudo().unlink()
        #add the new photo attachment
        attachment = None
        data = new_value.replace('data:image/png;base64,', '')
        try:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': str(line.a_tag) + '.png',
                'datas': bytes(data, encoding='utf8'),
                'datas_fname': str(line.a_tag) + '.png',
                'res_model': 'survey.user_input_line',
                'mimetype': 'image/png',
            })
        except Exception:
            _logger.exception("Fail to create cam attachment %s" % line.a_tag + '.png')
        line.write({
            'value_adv_mat_cam': attachment.id,
            'value_adv_mat': new_value,
        })

    def update_attachment(self,line,new_value):
        # unlink old attachments
        for attach in line.value_adv_mat_attachment:
            request.env['ir.attachment'].search([('id', '=', int(attach.id))]).sudo().unlink()
        # add new attachments
        files = request.httprequest.files.getlist(line.a_tag)
        model = request.env['ir.attachment']
        attachments_list = []
        for file in files:
            filename = file.filename
            try:
                attachment = model.create({
                    'name': filename,
                    'datas': base64.encodestring(file.read()),
                    'datas_fname': filename,
                    'res_model': model,
                    'mimetype': file.content_type,
                })
            except Exception:
                _logger.exception("Fail to upload attachment %s" % file.filename)
            else:
                attachments_list.append(attachment.id)
        line.write({
            'value_adv_mat_attachment': [(6, 0, attachments_list)],
            'value_adv_mat': str(attachments_list),
        })

    # We talk survey session here :
    # ============================

    # Survey start
    @http.route(['/survey/start/<model("survey.survey"):survey>',
                 '/survey/start/<model("survey.survey"):survey>/<model("spc_survey.session.info"):survey_session_info>',
                 '/survey/start/<model("survey.survey"):survey>/<string:token>',
                 ],
                type='http', auth='public', website=True)
    def start_survey(self, survey, survey_session_info=None, token=None, **post):
        UserInput = request.env['survey.user_input']
        # Test mode
        if token and token == "phantom":
            _logger.info("[survey] Phantom mode")
            user_input = UserInput.create({'survey_id': survey.id, 'test_entry': True})
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.render('survey.survey_init', data)
        # END Test mode

        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(survey, token=token)
        if errpage:
            return errpage

        # Manual surveying
        if not token:
            vals = {'survey_id': survey.id}
            #in case of session
            if survey_session_info:
                vals.update({'survey_session_info_id' : survey_session_info.id})
            ###################
            if not request.env.user._is_public():
                vals['partner_id'] = request.env.user.partner_id.id
            user_input = UserInput.create(vals)
        else:
            user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
            if not user_input:
                return request.render("survey.403", {'survey': survey})

        # Do not open expired survey
        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # Intro page
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            # in case of session
            if survey_session_info:
                data.update({'survey_session_info':survey_session_info})
            #######################
            return request.render('survey.survey_init', data)
        else:
            return request.redirect('/survey/fill/%s/%s' % (survey.id, user_input.token))


    # Survey displaying
    @http.route(['/survey/fill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:token>/<model("spc_survey.session.info"):survey_session_info>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:token>/<string:prev>'],
                type='http', auth='public', website=True)
    def fill_survey(self, survey, token, survey_session_info=None, prev=None, **post):
        '''Display and validates a survey'''
        Survey = request.env['survey.survey']
        UserInput = request.env['survey.user_input']
        # Controls if the survey can be displayed
        errpage = self._check_bad_cases(survey)
        if errpage:
            return errpage

        # Load the user_input
        user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
        if not user_input:  # Invalid token
            return request.render("survey.403", {'survey': survey})

        # Do not display expired survey (even if some pages have already been
        # displayed -- There's a time for everything!)
        errpage = self._check_deadline(user_input)
        if errpage:
            return errpage

        # Select the right page
        if user_input.state == 'new':  # First page
            page, page_nr, last = Survey.next_page(user_input, 0, go_back=False)
            data = {'survey': survey, 'page': page, 'page_nr': page_nr, 'token': user_input.token}
            # in case of session
            if survey_session_info:
                data.update({'survey_session_info': survey_session_info})
            # in case of session
            if last:
                data.update({'last': True})
            return request.render('survey.survey', data)
        elif user_input.state == 'done':  # Display success message
            # in case of session
            sfinished_data = {'survey': survey, 'token': token, 'user_input': user_input}
            if survey_session_info:
                sfinished_data.update({'survey_session_info': survey_session_info})
            # in case of session
            return request.render('survey.sfinished', sfinished_data)
        elif user_input.state == 'skip':
            flag = (True if prev and prev == 'prev' else False)
            page, page_nr, last = Survey.next_page(user_input, user_input.last_displayed_page_id.id, go_back=flag)
            #special case if you click "previous" from the last page, then leave the survey, then reopen it from the URL, avoid crash
            if not page:
                page, page_nr, last = Survey.next_page(user_input, user_input.last_displayed_page_id.id, go_back=True)
            data = {'survey': survey, 'page': page, 'page_nr': page_nr, 'token': user_input.token}
            if survey_session_info:
                data.update({'survey_session_info': survey_session_info})
            if last:
                data.update({'last': True})
            return request.render('survey.survey', data)
        else:
            return request.render("survey.403", {'survey': survey})


    # AJAX submission of a page
    @http.route(['/survey/submit/<model("survey.survey"):survey>'], type='http', methods=['POST'], auth='public', website=True)
    def submit(self, survey, **post):
        page_id = int(post['page_id'])
        questions = request.env['survey.question'].search([('page_id', '=', page_id)])

        # Answer validation
        errors = {}
        for question in questions:
            answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
            errors.update(question.validate_question(post, answer_tag))
        ret = {}
        if len(errors):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            # Store answers into database
            try:
                user_input = request.env['survey.user_input'].sudo().search([('token', '=', post['token'])], limit=1)
            except KeyError:  # Invalid token
                return request.render("survey.403", {'survey': survey})
            user_id = request.env.user.id if user_input.type != 'link' else SUPERUSER_ID
            for question in questions:
                answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
                request.env['survey.user_input_line'].sudo(user=user_id).save_lines(user_input.id, question, post, answer_tag)
            go_back = post['button_submit'] == 'previous'
            next_page, _, last = request.env['survey.survey'].next_page(user_input, page_id, go_back=go_back)
            vals = {'last_displayed_page_id': page_id}
            if next_page is None and not go_back:
                vals.update({'state': 'done'})
            else:
                vals.update({'state': 'skip'})
            user_input.sudo(user=user_id).write(vals)
            ret['redirect'] = '/survey/fill/%s/%s' % (survey.id, post['token'])
            if 'survey_session_info_hidden' in post:
                ret['redirect'] += '/' + post['survey_session_info_hidden']
            if go_back:
                ret['redirect'] += '/prev'
        return json.dumps(ret)

    # scoring
    @http.route('/survey/scoring/<model("survey.survey"):survey>/<string:token>', type='http', auth="public", website=True)
    def scoring(self, survey=None, token=None, **post):
        request.env['survey.user_input'].search([('token', '=', token)]).calculate_scores()
        session_info = request.env['survey.user_input'].search([('token', '=', token)]).survey_session_info_id
        session_info.write({
            'closing_date' : datetime.today()
        })
        vals = ({
                'token': token
                })
        return request.render("spc_survey.single_survey_scores", vals)

    # /survey/end_session/
    @http.route('/survey/end_session/<string:token>', type='http', auth="public", website=True)
    def session_scores(self, token=None, **kwargs):
        menu_id = request.env.ref('survey.menu_surveys').id
        action_id = request.env.ref('survey.action_survey_user_input').id
        resp_id = request.env['survey.user_input'].search([('token', '=', token)]).id
        return request.redirect('/web#id=%s&action=%s&model=survey.user_input&view_type=form&menu_id=%s' % (str(resp_id), str(action_id), str(menu_id)))


    #web view answers
    # example : survey/print/prop-org-1/703d6d15-33d5-47e7-a4bf-d2acacfaa560/view_answers
    @http.route(['/survey/print/<model("survey.survey"):survey>/<string:token>/view_answers'], type='http', auth="public",
                    website=True)
    def view_answers(self, survey, token, **post):
        vals = ({
            'edit': False,
            'token': token,
            'survey': survey,
        })
        return request.render("survey.survey_print", vals)
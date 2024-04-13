# -*- coding: utf-8 -*-
from odoo import models,api
import logging


class ColumnTypeModelRpc(models.Model):

    _name = "column_type_model.rpc"
    _description = "used for column type [model] linked with the rpc method"

    @api.model 
    def get_model_records(self,model,token,question,column,filter_field,is_filter_on,filter_value):
        survey_user_input_id = self.env['survey.user_input'].search([('token','=',token)])
        survey_id = survey_user_input_id.survey_id
        list_m1_to_hide = []
        if self.env['spc_survey_extra.control_m_m1'].search([('survey_id','=',survey_id.id)]):
            list_control_m_m1 = self.env['spc_survey_extra.control_m_m1'].search([('survey_id', '=', survey_id.id)])
            if survey_user_input_id.survey_session_info_id:
                if survey_user_input_id.survey_session_info_id.site_id:  #coming from planing
                    previous_sessions_infos_list = self.env['spc_survey.session.info'].search(['&','&',('survey_session_id','=',survey_user_input_id.survey_session_info_id.survey_session_id.id),('site_id','!=',False),('closing_date','!=',False)])
                    closing_date = previous_sessions_infos_list[0].closing_date
                    previous_session_info = survey_user_input_id.survey_session_info_id
                    for survey_session_info in previous_sessions_infos_list:
                        if survey_session_info == previous_session_info:
                            continue
                        if closing_date < survey_session_info.closing_date:
                            closing_date = survey_session_info.closing_date
                            previous_session_info = survey_session_info
                    previous_survey_user_input = self.env['survey.user_input'].search([('survey_session_info_id','=',previous_session_info.id)])
                else: #session test
                    previous_sessions_infos_list = self.env['spc_survey.session.info'].search(['&','&',('survey_session_id','=',survey_user_input_id.survey_session_info_id.survey_session_id.id),('site_id','=',False),('closing_date','!=',False)])
                    closing_date = previous_sessions_infos_list[0].closing_date
                    previous_session_info = survey_user_input_id.survey_session_info_id
                    for survey_session_info in previous_sessions_infos_list:
                        if survey_session_info == previous_session_info:
                            continue
                        if closing_date < survey_session_info.closing_date:
                            closing_date = survey_session_info.closing_date
                            previous_session_info = survey_session_info
                    previous_survey_user_input = self.env['survey.user_input'].search([('survey_session_info_id', '=', previous_session_info.id)])

            else: #not a session
                survey_user_input_list = self.env['survey.user_input'].search([('survey_id','=',survey_user_input_id.survey_id.id),('survey_session_info_id','=',False)])
                closing_date = survey_user_input_list[0].date_create
                previous_survey_user_input = survey_user_input_id
                for survey_user_input in survey_user_input_list:
                    if survey_user_input_id != survey_user_input:
                        continue
                    if closing_date < survey_user_input.date_create:
                        closing_date = survey_user_input.date_create
                        previous_survey_user_input = survey_user_input

            for rec in list_control_m_m1:
                if question == str(rec.survey_id.id) + '_' + str(rec.question_id.page_id.id) + '_' + str(rec.question_id.id):
                    concerned_questions = rec.concerned_questions_ids
                    for question in concerned_questions:
                        if column == question.column_id.value:
                            if question.question_or_detail == 'detail':
                                for rec in self.env['survey.user_input_line'].search(['&','&',('user_input_id','=',previous_survey_user_input.id),('question_id','=',question.question_id.id),'&',('column','=',str(question.column_id.value)),('a_tag','=ilike','_details')]):
                                    list_m1_to_hide.append(rec.value_adv_mat)
                            else: #question_or_detail == 'question'
                                for rec in self.env['survey.user_input_line'].search(['&','&',('user_input_id','=',previous_survey_user_input.id),('question_id','=',question.question_id.id),'&',('column','=',str(question.column_id.value)),('a_tag','not ilike','_details')]):
                                    list_m1_to_hide.append(rec.value_adv_mat)
                        else:
                            list_m1_to_hide = []
        else: #no control_m_m1 detected
            list_m1_to_hide = []
        list_records = []
        result = []
        model2 = ""
        field_type = ""
        if filter_field and is_filter_on == 'undefined' : #filter input case (is_filter_on is an main input attribute)
            for name, field in self.env[model]._fields.items():
                if name == filter_field:
                    if field.type == 'many2one':
                        model = field.comodel_name
                    else:
                        if field.type == 'selection':
                            result = [elem[0] for elem in field.selection]
                            return result
                        return []

        if filter_field and is_filter_on == '1':  # main input case
            for name, field in self.env[model]._fields.items():
                if name == filter_field:
                    if field.type == 'many2one':
                        model2 = field.comodel_name
                    else:
                        model2 = model
                    field_type = field.type

        if is_filter_on == "1": #main search input
            if filter_value != "undefined":
                domain = self.get_suitable_domain(model2, filter_value,field_type)
                list_records = self.env[model].search([(filter_field,'in',domain)])
        if (filter_field in ["","undefined"] or is_filter_on in ["0","undefined"]) and model2 != model: #no filter_field case or filter is not on (case of main input)
            list_records = self.env[model].search([])
        for rec in list_records:
            result.append(rec.name_get()[0][1])
        if list_m1_to_hide:
            for rec in list_m1_to_hide:
                result.remove(rec)
        return result


    @api.model
    def check_in_model_recorde(self, model, input_value, filter_field, is_filter_on):
        list_records = []
        if filter_field and is_filter_on in ['undefined','0'] : #filter input case
            for name, field in self.env[model]._fields.items():
                if name == filter_field:
                    if field.type == 'many2one':
                        model = field.comodel_name
                    else: #other types
                        return 1
        list_records = self.env[model].search([])

        for rec in list_records:
            if rec.name_get()[0][1] == input_value:
                return 1
        return 0

    def get_suitable_domain(self,model,filter_value,field_type):
        domain = []
        model_rec_name = self.env[model]._rec_name
        if field_type == 'many2one':
            domain = self.env[model].search([(model_rec_name, '=', filter_value)]).ids
        if field_type in ['char', 'datetime', 'date', 'selection', 'text', 'html']:
            domain = [str(i) for i in filter_value.split(',')]
        if field_type in ['boolean']:
            domain = [bool(filter_value)]
        if field_type in ['integer']:
            domain = [int(i) for i in filter_value.split(',')]
        if field_type in ['float']:
            domain = [float(i) for i in filter_value.split(',')]
        return domain
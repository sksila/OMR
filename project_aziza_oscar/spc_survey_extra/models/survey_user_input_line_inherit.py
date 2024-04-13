import base64
import logging
import re

from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _


class SurveyExtraUserInputLineInherit(models.Model):
    _inherit = "survey.user_input_line"

    value_adv_mat_model = fields.Text(string='Advanced Matrix model answer')
    value_adv_mat_field_model = fields.Text(string="Advanced Matrix field_model answer")
    type_resp = fields.Selection(selection_add=[("model", _("Model")), ("field_model", _("Field model"))])

    def save_model(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            vals.update({
                'value_adv_mat_model': post[a_tag],
                'value_adv_mat': post[a_tag],
            })
        return vals

    def save_field_model(self,post,a_tag, vals):
        vals.update({
            'value_adv_mat_field_model': post[a_tag],
            'value_adv_mat': post[a_tag],
        })
        return vals

    @api.model
    def save_line_advanced_matrix(self, user_input_id, question, post, answer_tag):
        vals = {
            "user_input_id": user_input_id,
            "question_id": question.id,
            'answer_type': 'adv_mat',
        }

        comment_answer = "%s_%s" % (answer_tag, 'comment')
        if comment_answer in post:
            vals.update({
                'a_tag': comment_answer,
                'type_resp': 'text',
                'value_adv_mat': post[comment_answer]
            })
            self.create(vals)
            post.pop(comment_answer)


        done_a_tags = []
        cols_type_resp = {}
        counter = 0
        for col in question.labels_adv_matrix_cols_ids:
            counter += 1
            cols_type_resp[col.id] = col.col_type_resp #add line row
            if question.labels_adv_matrix_rows_ids:
                for row in question.labels_adv_matrix_rows_ids:
                    a_tag = "%s_%s_%s" % (answer_tag, row.id, col.id)
                    if a_tag in post:
                        done_a_tags.append(a_tag)
                        try:
                            saver = getattr(self, 'save_' + col.col_type_resp)
                        except AttributeError:
                            _logger.warning(col.col_type_resp + ": This type of question has no save method")
                            return {}
                        else:
                            vals.update({
                                'a_tag': a_tag,
                                'type_resp': col.col_type_resp,
                                'column': col.value,
                                'row': row.value
                            })
                            returned_vals = saver(post, a_tag, vals)
                            self.create(returned_vals)

                #add_line
                if counter == len(question.labels_adv_matrix_cols_ids) and question.add_line_feature:
                    for element in post:
                        if element not in done_a_tags and answer_tag in element and not re.search("[a-zA-Z]", element) and '_details' not in element:
                            for colum in cols_type_resp:
                                if element.endswith(str(colum)):
                                    try:
                                        saver = getattr(self, 'save_' + cols_type_resp[colum])
                                    except AttributeError:
                                        _logger.warning(cols_type_resp[colum] + ": This type of question has no save method")
                                        return {}
                                    else:
                                        vals.update({
                                                'a_tag': element,
                                                'type_resp': cols_type_resp[colum],
                                                'column': colum,
                                                'row': element.split('_')[3]
                                            })
                                        returned_vals = saver(post, element, vals)
                                        self.create(returned_vals)
                                        break

            else:  # automatic fill case
                auto_fill_key = "automatic_fill_%s" % (answer_tag)
                for row in range(int(post[auto_fill_key])):
                    a_tag = "%s_%s_%s" % (answer_tag, str(row), col.id)
                    if a_tag in post:
                        try:
                            saver = getattr(self, 'save_' + col.col_type_resp)
                        except AttributeError:
                            _logger.warning(col.col_type_resp + ": This type of question has no save method")
                            return {}
                        else:
                            vals.update({
                                'a_tag': a_tag,
                                'type_resp': col.col_type_resp,
                                'column': col.value,
                                'row': str(row)
                            })
                            returned_vals = saver(post, a_tag, vals)
                            self.create(returned_vals)

        if question.detail:
            vals = {
                "user_input_id": user_input_id,
                "question_id": question.id,
                'answer_type': 'adv_mat',
            }
            detail_list = []
            details_cols_type_resp = {}
            for element in post:
                if '_details' in element:
                    detail_list.append(element)
            for col in question.detail_labels_adv_matrix_cols_ids:
                details_cols_type_resp[col.id] = col.col_type_resp
            for element in detail_list:
                for elem in details_cols_type_resp:
                    if element.split('_')[4] == str(elem):
                        try:
                            saver = getattr(self, 'save_' + details_cols_type_resp[elem])
                        except AttributeError:
                            _logger.warning(cols_type_resp[colum] + ": This type of question has no save method")
                            return {}
                        else:
                            vals.update({
                                'a_tag': element,
                                'type_resp': details_cols_type_resp[elem],
                                'column': elem,
                                'row': element.split('_')[3]
                            })
                            returned_vals = saver(post, element, vals)
                            self.create(returned_vals)
                            break











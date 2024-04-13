import base64
import logging

from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _


class SurveyUserInputLineInherit(models.Model):
    _inherit = "survey.user_input_line"

    answer_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('free_text', 'Free Text'),
        ('suggestion', 'Suggestion'),
        ('adv_mat','Advanced Matrix field')], string='Answer Type')

    value_adv_mat_text = fields.Char('Advanced Matrix Text answer')
    value_adv_mat_textarea = fields.Text('Advanced Matrix Textarea answer')
    value_adv_mat_number = fields.Integer('Advanced Matrix Number answer')
    value_adv_mat_float_number = fields.Float('Advanced Matrix FloatNumber answer')
    value_adv_mat_date = fields.Date('Advanced Matrix Date answer')
    value_adv_mat_dropdown = fields.Char('Advanced Matrix Dropdown answer')
    value_adv_mat_attachment = fields.Many2many('ir.attachment', 'survey_user_input_line_ir_attachments_rel',
                                                    'survey_user_input_line_id', 'attachment_id',
                                                string='Advanced Matrix Attachments answer')
    value_adv_mat_cam = fields.Many2one('ir.attachment', string='Advanced Matrix cam answer')
    value_adv_mat = fields.Char('Advance Matrix answer')

    type_resp = fields.Selection([
        ("text", _("Text")),
        ("textarea", _("Multilines text")),
        ("number", _("Number")),
        ("float_number", _("Float number")),
        ("date", _("Date")),
        ("dropdown", _("Dropdown")),
        ("attachment", _("Attachment")),
        ("cam", _("Camera"))], string="Response type")

    a_tag = fields.Char("Answer tag")
    column = fields.Char("Answer column")
    row = fields.Char("Answer row")

    @api.constrains('answer_type')
    def _check_answer_type(self):
        for uil in self:
            fields_type = {
                'text': bool(uil.value_text),
                'number': (bool(uil.value_number) or uil.value_number == 0),
                'date': bool(uil.value_date),
                'free_text': bool(uil.value_free_text),
                'suggestion': bool(uil.value_suggested),
                'adv_mat' : (bool(uil.value_adv_mat) or uil.value_adv_mat == '')
            }
            if not fields_type.get(uil.answer_type, True):
                raise ValidationError(_('The answer must be in the right type'))

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

        for col in question.labels_adv_matrix_cols_ids:
            if question.labels_adv_matrix_rows_ids:
                for row in question.labels_adv_matrix_rows_ids:
                    a_tag = "%s_%s_%s" % (answer_tag, row.id, col.id)
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
                                'column' : col.value,
                                'row' : row.value
                            })
                            returned_vals = saver(post, a_tag, vals)
                            self.create(returned_vals)
            else: #automatic fill case in spc_survey_extra_module
                pass


    def save_text(self,post,a_tag, vals):
        vals.update({
            'value_adv_mat_text': post[a_tag],
            'value_adv_mat': post[a_tag],
        })
        return vals


    def save_textarea(self,post,a_tag, vals):
        vals.update({
            'value_adv_mat_textarea': post[a_tag],
            'value_adv_mat': post[a_tag],
        })
        return vals

    def save_number(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            vals.update({
                'value_adv_mat_number': int(post[a_tag]),
                'value_adv_mat': post[a_tag],
            })
        return vals

    def save_float_number(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            vals.update({
                'value_adv_mat_float_number': float(post[a_tag]),
                'value_adv_mat': post[a_tag],
            })
        return vals

    def save_date(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            vals.update({
                'value_adv_mat_date': post[a_tag],
                'value_adv_mat': post[a_tag],
            })
        return vals

    def save_dropdown(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            vals.update({
                'value_adv_mat_dropdown': post[a_tag],
                'value_adv_mat': post[a_tag],
            })
        return vals

    def save_attachment(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': '',
                'value_adv_mat_attachment': False
            })
        else:
            files = request.httprequest.files.getlist(a_tag)
            model = self.env['ir.attachment']
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
            vals.update({
                'value_adv_mat_attachment': [(6,0,attachments_list)],
                'value_adv_mat': str(attachments_list),
            })
            attachments_list = []
        return vals

    def save_cam(self,post,a_tag, vals):
        if not post[a_tag]: #empty
            vals.update({
                'value_adv_mat': post[a_tag],
            })
        else:
            model = self.env['ir.attachment']
            attachment = None
            data = post[a_tag].replace('data:image/png;base64,','')
            try:
                attachment = model.create({
                    'name': str(a_tag) + '.png',
                    'datas': bytes(data, encoding='utf8'),
                    'datas_fname': str(a_tag) + '.png',
                    'res_model': 'survey.user_input_line',
                    'mimetype': 'image/png',
                })
            except Exception:
                _logger.exception("Fail to create cam attachment %s" % a_tag + '.png')
            vals.update({
                'value_adv_mat_cam': attachment.id,
                'value_adv_mat': post[a_tag],
            })
        return vals


# -*- coding: utf-8 -*-
import logging

from odoo import api ,models, fields, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import ValidationError, UserError


class SpcSurveyMailActivity(models.Model):
    _inherit = "mail.activity"

    def is_only_auditor_status(self):
        if self.env.user.has_group('spc_survey.group_auditor') and not self.env.user.has_group('spc_survey.group_audit_manager'):
            return True
        return False

    resource_ref = fields.Reference(string='Référence', selection='_selection_target_model_survey')
    survey_type_id = fields.Many2one(comodel_name='spc_survey.type', string='Survey type')
    is_survey_session = fields.Boolean(compute='is_survey_session_status', default=False)
    is_only_auditor = fields.Boolean(default=is_only_auditor_status)
    survey_type_id = fields.Many2one(comodel_name='spc_survey.type', string='Survey type', compute="get_survey_type_id")

    @api.model
    def _selection_target_model_survey(self):
        models = self.env['ir.model'].search([])
        if self.env.user.has_group('spc_survey.group_auditor') and not self.env.user.has_group('spc_survey.group_audit_manager'):
            models = self.env['ir.model'].search([('model','=','spc_survey.session')])
        return [(model.model, model.name) for model in models]

    @api.multi
    def action_close_dialog(self):
        self.ensure_one()

        concerned_session_info = self.env['spc_survey.session.info'].sudo().search([('activity_id','=',self.id),('closing_date','!=',False)], limit=1)
        if concerned_session_info:
            raise ValidationError(_('Session already done.'))

        url = self.resource_ref.survey_ids[0].public_url
        # create survey session info:
        survey_session_info_id = self.env['spc_survey.session.info'].sudo().create({
            'opening_date': fields.Datetime.now(),
            'name': self.resource_ref.name,
            'site_id': self.site_id.id,
            'auditor_id': self.user_id.id,
            'activity_id': self.id,
            'survey_session_id': self.resource_ref.id
        })
        return {
            'type': 'ir.actions.act_url',
            'name': "Launch survey session",
            'target': 'self',
            'url': str(self.resource_ref.survey_ids[0].with_context(relative_url=True).public_url) + "/" + str(
                slug(survey_session_info_id))
        }

    @api.multi
    @api.depends('resource_ref')
    def is_survey_session_status(self):
        for rec in self:
            if 'spc_survey.session' in str(rec.resource_ref):
                rec.is_survey_session = True


    @api.multi
    @api.depends('resource_ref')
    def get_survey_type_id(self):
        for rec in self:
            if 'spc_survey.session' in str(rec.resource_ref):
                rec.survey_type_id = rec.resource_ref.survey_type_id.id


    @api.multi
    def write(self, vals):
        if self.is_survey_session:
            for survey in self.resource_ref.survey_ids:
                if survey.stage_id != self.env.ref('survey.stage_permanent'):
                    raise UserError(_("La maquette %s n'est pas à l'état validé" %(survey.title)))
            return super().write(vals)
        else:
            return super().write(vals)


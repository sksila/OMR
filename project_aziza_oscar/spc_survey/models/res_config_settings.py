

from odoo import api, fields, models, http


class SpcSurveyConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_survey_session = fields.Boolean(string="Enable survey session", default=False)

    def set_values(self):
        res = super(SpcSurveyConfigSettings, self).set_values()
        params = self.env["ir.config_parameter"].sudo()
        if self.enable_survey_session:
            params.set_param("spc_survey.enable_survey_session", True)
            self.env.ref('spc_survey.menu_spc_survey_session').write({
                'groups_id': [(6, 0, [self.env.ref('spc_survey.group_audit_manager').id, self.env.ref('spc_survey.group_audit_consulting').id])]
            })
        else:
            params.set_param("spc_survey.enable_survey_session", False)
            self.env.ref('spc_survey.menu_spc_survey_session').write({
                'groups_id': [(6, 0, [self.env.ref('spc_survey.make_invisible').id])]
            })
        return res

    @api.model
    def get_values(self):
        res = super(SpcSurveyConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        enable_survey_session_value = params.get_param("spc_survey.enable_survey_session")
        res.update(enable_survey_session =enable_survey_session_value)
        return res


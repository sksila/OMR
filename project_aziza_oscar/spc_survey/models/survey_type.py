
from odoo import api, fields, models, _


class SpcSurveyType(models.Model):
    _name = "spc_survey.type"
    _description = "Type de maquette"

    def _default_module_spc_survey_category_domain(self):
        return [('category_id', '=', self.env.ref('spc_survey.module_spc_survey_category').id)]

    name = fields.Char(string='Name', required=True)
    group_ids = fields.Many2many('res.groups', 'res_groups_spc_survey_type', 'type_id', 'group_id', string='Groups', domain=lambda self : self._default_module_spc_survey_category_domain())
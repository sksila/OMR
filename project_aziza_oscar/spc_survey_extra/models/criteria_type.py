from odoo import fields, models, api


class CriteriaType (models.Model):
    _name = 'spc_survey_extra.criteria_type'
    _description = "Type de critére"

    name = fields.Char("Name", required=True)
    



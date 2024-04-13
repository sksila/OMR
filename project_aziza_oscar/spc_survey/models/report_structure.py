from odoo import api, fields, models, _
import logging


class SpcSurveyReportStructure(models.Model):
    _name = "spc_survey.report_structure"
    _description = "Structure du rapport final de session"

    name = fields.Char('Title', required=True)
    line_title = fields.Char('Line title')
    column1 = fields.Char('Column1')
    column2 = fields.Char('Column2')
    column3 = fields.Char('Column3')
    column4 = fields.Char('Column4')
    column5 = fields.Char('Column5')
    column6 = fields.Char('Column6')
    detail_ids = fields.One2many('spc_survey.report_structure_details','report_structure_id', string="Details")
    survey_session_id = fields.Many2one('spc_survey.session')
    domain_columns = fields.Many2many('spc_survey.session_scoring',  'rel_domain_columns', compute="get_domain_columns")

    @api.depends('survey_session_id')
    @api.one
    def get_domain_columns(self):
        columns_list = []
        for line in self.survey_session_id.session_scoring_ids:
            columns_list.append(line.id)
        self.domain_columns = [(6, 0, columns_list)]


class SpcSurveyReportStructureDetails(models.Model):
    _name = "spc_survey.report_structure_details"
    _description = "Détails de structure du rapport final de session"

    column_title = fields.Char('Line title')
    column1_id = fields.Many2one('spc_survey.session_scoring', string="Column1")
    column2_id = fields.Many2one('spc_survey.session_scoring', string="Column2")
    column3_id = fields.Many2one('spc_survey.session_scoring', string="Column3")
    column4_id = fields.Many2one('spc_survey.session_scoring', string="Column4")
    column5_id = fields.Many2one('spc_survey.session_scoring', string="Column5")
    column6_id = fields.Many2one('spc_survey.session_scoring', string="Column6")
    report_structure_id = fields.Many2one('spc_survey.report_structure')
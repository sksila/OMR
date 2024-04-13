# -*- coding: utf-8 -*-

'''
Anything about survey.stage model will be handled here
'''

from odoo import api, fields, models, _


class SpcSurveyStage(models.Model):

    _inherit = "survey.stage"

    @api.model
    def _invoke_update_stages(self):
        #permanent status
        permanent_stage_id = self.env.ref('survey.stage_permanent')
        permanent_stage_id.write({'name': 'Validé'})

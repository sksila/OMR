from odoo import api, fields, models, _


class SpcSurveyAzizaObjectifs(models.Model):
    _name = "audit.objectif"
    _description = "Objectif model"
    _rec_name = "action"

    action = fields.Char('Action')
    objectif = fields.Float('Objectif')
    user_id = fields.Many2one('res.users', string="Utilisateur")
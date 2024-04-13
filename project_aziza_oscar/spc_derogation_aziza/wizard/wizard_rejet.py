# -*- coding: utf-8 -*-

from odoo import models, fields, api

TYPE_REJET_SELECTION = [
    ('reject', "Rejet"),
    ('reset', "Remettre")]


class RejetWizard(models.TransientModel):
    _name = 'rejet.wizard'
    _description = 'Rejet Wizard'

    @api.model
    def default_get(self, fields):

        result = super(RejetWizard, self).default_get(fields)
        if self._context.get('active_id'):
            derogation = self.env['derogation.derogation'].browse(self._context['active_id'])
            result['derogation_id'] = derogation.id
        return result

    derogation_id = fields.Many2one('derogation.derogation', "Dérogation", required=True)
    motif_rejet = fields.Text("Motif", required=True)
    date_rejet = fields.Date('Date', default=fields.Date.today())
    type_rejet = fields.Selection(TYPE_REJET_SELECTION, string='Type rejet', readonly=True)

    def action_confirm(self):
        if self.type_rejet == 'reject':
            self.derogation_id.write({'state': 'rejected', 'motif_rejet': self.motif_rejet, 'date_rejet': self.date_rejet})
        elif self.type_rejet == 'reset':
            vals = {'name': self.motif_rejet,
                    'date_reset': self.date_rejet,
                    'user_id': self.env.user.id,
                    'derogation_id': self.derogation_id.id
                    }
            self.env['derogation.reset'].create(vals)
            self.derogation_id.write({'state': 'draft'})
        return

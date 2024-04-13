# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

TYPE_REJET_SELECTION = [
    ('reject', "Rejet"),
    ('reset', "Remettre")]

class RejetWizard(models.TransientModel):
    # region Private attributes
    _name = 'oscar.rejet.wizard'
    _description = 'Rejet Wizard'

    # region Default methods
    @api.model
    def default_get(self, fields):
        result = super(RejetWizard, self).default_get(fields)
        if self._context.get('active_id'):
            dispatch = self.env['oscar.dispatch'].browse(self._context['active_id'])
            result['dispatch_id'] = dispatch.id
        return result

    # endregion

    # region Fields declaration
    dispatch_id = fields.Many2one('oscar.dispatch', "Dispatching", required=True)
    motif_rejet = fields.Text("Motif", required=True)
    date_rejet = fields.Date('Date', default=fields.Date.today())
    type_rejet = fields.Selection(TYPE_REJET_SELECTION, string='Type rejet', readonly=True)
    # endregion

    # region Actions
    def action_confirm(self):
        if self.type_rejet == 'reject':
            self.dispatch_id.write({'state': 'rejected', 'motif_rejet': self.motif_rejet, 'date_rejet': self.date_rejet})
        elif self.type_rejet == 'reset':
            vals = {'name': self.motif_rejet,
                    'date_reset': self.date_rejet,
                    'user_id': self.env.user.id,
                    'dispatch_id': self.dispatch_id.id
                }
            self.env['oscar.dispatch.reset'].create(vals)
            self.dispatch_id.write({'state': 'draft'})
        return
    # endregion
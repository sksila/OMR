# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

STATE_JOURNEE_SELECTION = [
    ('new', 'En préparation'),
    ('prepared', 'Clôturée'),
    ('road','En route'),
    ('done1','Reçue à l\'entrepôt'),
    ('done','Reçue au siège'),
    ('waiting','En attente'),
    ('accepted','Acceptée'),
    ('waiting2','En attente la deuxième vérification'),
    ('accepted1','Acceptée TR'),
    ('waiting1','En attente avec litige'),
    ('checked','Vérifiée'),
]

class ChangeStatusJourneeWizard(models.TransientModel):
    _name = "change.state.journee.wizard"
    _description = "Changer le statut de la journée Wizard"

    @api.model
    def default_get(self, fields):
        result = super(ChangeStatusJourneeWizard, self).default_get(fields)
        if self._context.get('active_id'):
            journee = self.env['oscar.journee'].browse(self._context['active_id'])
            result['journee_id'] = journee.id
            result['state'] = journee.state
        return result

    journee_id = fields.Many2one('oscar.journee', string="Journée")
    state = fields.Selection(STATE_JOURNEE_SELECTION, string='Statut')

    @api.multi
    def set_state_journee(self):
        has_group_admin = self.env.user.has_group('spc_oscar_aziza.group_admin_oscar')
        vals = {
            'state':self.state,
        }
        if has_group_admin:
            self.journee_id.write(vals)
        else:
            raise ValidationError(_("Vous n'avez pas le droit pour modifier le statut de la journée!"))
        return True

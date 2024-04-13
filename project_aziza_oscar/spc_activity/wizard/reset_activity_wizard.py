# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from calendar import monthrange

_logger = logging.getLogger(__name__)


class ResetActivity(models.TransientModel):
    _name = 'reset.activity.wizard'
    _description = "Réinitialiser l'activité Wizard"

    @api.model
    def default_get(self, fields):
        result = super(ResetActivity, self).default_get(fields)
        if self._context.get('active_id'):
            activity = self.env['mail.activity'].browse(self._context['active_id'])
            result['activity_id'] = activity.id
        return result

    activity_id = fields.Many2one('mail.activity', string='Activité', readonly=True)
    motif_id = fields.Many2one('spc.activity.motif', "Motif", index=True)
    other = fields.Boolean('Autre')
    comment = fields.Text('Description')

    def action_confirm(self):
        vals = {
            'name': self.motif_id.name or self.comment,
            'date_reset': datetime.now(),
            'user_id': self.env.user.id,
            'activity_id': self.activity_id.id,
            }

        self.env['spc.activity.reset'].create(vals)
        self.activity_id.write({'workflow_activity': 'new'})
        return True


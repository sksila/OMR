# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ChangeSourceWizard(models.TransientModel):
    _name = "change.source.wizard"
    _description = "Changer le source Wizard"

    @api.model
    def default_get(self, fields):
        result = super(ChangeSourceWizard, self).default_get(fields)
        if self._context.get('model_type') and self._context.get('active_id'):
            model_type = self._context.get('model_type')
            result['type'] = model_type
            if model_type == 'envelope':
                envelope = self.env['oscar.envelope'].browse(self._context['active_id'])
                result['envelope_id'] = envelope.id
                result['source_id'] = envelope.source_id.id
                result['destinataire_id'] = envelope.destinataire_id.id
            elif model_type == 'bordereau':
                bordereau = self.env['oscar.bordereau'].browse(self._context['active_id'])
                result['bordereau_id'] = bordereau.id
                result['source_id'] = bordereau.source_id.id
                result['destinataire_id'] = bordereau.destinataire_id.id
        return result

    type = fields.Selection([
        ('envelope', 'Enveloppe'),
        ('bordereau', 'Bordereau'),
    ], string='Enveloppe/Bordereau')
    envelope_id = fields.Many2one('oscar.envelope', string="Enveloppe")
    bordereau_id = fields.Many2one('oscar.bordereau', string="Bordereau")
    source_id = fields.Many2one('oscar.site', string="Source", domain=[('site_type', 'in', ['MAGASIN', 'CENTRALE'])])
    destinataire_id = fields.Many2one('oscar.site', string="Destinataire",
                                      domain=[('site_type', 'in', ['MAGASIN', 'CENTRALE'])])

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'bordereau':
            return {'domain': {'source_id': [('site_type', 'in', ['MAGASIN', 'ENTREPOT', 'CENTRALE'])],
                               'destinataire_id': [('site_type', 'in', ['MAGASIN', 'ENTREPOT', 'CENTRALE'])]}}
        elif self.type == 'envelope':
            return {'domain': {'source_id': [('site_type', 'in', ['MAGASIN', 'CENTRALE'])],
                               'destinataire_id': [('site_type', 'in', ['MAGASIN', 'CENTRALE'])]}}

    @api.multi
    def set_source_envelope(self):
        has_group_admin = self.env.user.has_group('spc_oscar_aziza.group_admin_oscar')
        vals = {
            'source_id': self.source_id.id,
            'destinataire_id': self.destinataire_id.id,
        }

        if has_group_admin:
            if self.type == 'envelope':
                self.envelope_id.write(vals)
            elif self.type == 'bordereau':
                self.bordereau_id.write(vals)
        else:
            raise ValidationError(_("Vous n'avez pas le droit pour modifier la source de document!"))
        return True

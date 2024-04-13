# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RefuseLitigeWizard(models.TransientModel):
    _name = "refuse.litige.wizard"
    _description = "Refuser le litige Wizzard"

    @api.model
    def default_get(self, fields):
        result = super(RefuseLitigeWizard, self).default_get(fields)
        if self._context.get('active_id'):
            litige_line = self.env['oscar.litige.line'].browse(self._context['active_id'])
            result['litige_line_id'] = litige_line.id
            result['currency_id'] = litige_line.currency_id.id
            result['litige'] = litige_line.litige
            result['est_ecart'] = litige_line.est_ecart
            result['state'] = litige_line.state
        return result


    litige_line_id = fields.Many2one('oscar.litige.line', string="Détail de litige")
    name = fields.Many2one('moyen.paiement', string='Mode de paiement', related="litige_line_id.name")
    motif_id = fields.Many2one('oscar.litige.motif',string="Motif")
    other = fields.Boolean("Autre", related="motif_id.other")
    comment = fields.Text("Commentaire")
    currency_id = fields.Many2one('res.currency', string='Currency')
    litige = fields.Monetary(string='Litige', digits=(12, 3), readonly=True, currency_field='currency_id')
    corrected_amount = fields.Monetary(string='Montant corrigé', digits=(12, 3), currency_field='currency_id')
    est_ecart = fields.Boolean("Est écart")
    details = fields.Boolean("Détails")
    litige_wizard_line_ids = fields.One2many('refuse.litige.line.wizard', 'litige_wizard_id', string='Détails')
    state = fields.Selection([
        ('invalidate', 'Brouillon'),
        ('dismissed', 'Ecarté'),
        ('corrected', 'Corrigé'),
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
        ('done', 'Clôturé'),
    ], string='Statut')


    @api.multi
    def validate_litige(self):
        has_group_resp_financier = self.env.user.has_group('spc_recette_aziza.group_responsable_financier_oscar')
        has_group_boe = self.env.user.has_group('spc_oscar_aziza.group_bo_oscar')
        vals = {
            'motif_id':self.motif_id.id,
            'comment':self.comment,
        }
        if self.state == 'invalidate' and has_group_resp_financier:
            if self.details:
                if self.litige_wizard_line_ids:
                    montant_total = sum(line.montant for line in self.litige_wizard_line_ids)
                    if self.litige != montant_total:
                        raise ValidationError(_("Veuillez vérifier les montants de détails du litige !"))
                    update = True
                    for line in self.litige_wizard_line_ids:
                        est_ecart = False
                        if line.state == 'dismissed':
                            est_ecart = True
                        lines_val = {
                            'name': line.name.id,
                            'currency_id': line.currency_id.id,
                            'litige': line.montant,
                            'ecart_id': self.litige_line_id.ecart_id.id,
                            'user_id': self.env.user.id,
                            'journee_recue_id': self.litige_line_id.journee_recue_id.id,
                            'motif': self.litige_line_id.motif,
                            'motif_id': line.motif_id.id,
                            'comment': line.comment,
                            'state': line.state,
                            'est_ecart': est_ecart,
                        }
                        if update:
                            self.litige_line_id.write(lines_val)
                            update = False
                        else:
                            self.env['oscar.litige.line'].create(lines_val)

                else:
                    raise ValidationError(_("Veuillez remplir les détails du litige !"))
            else:
                vals.update({'state':'dismissed','est_ecart':True})
                self.litige_line_id.write(vals)
        elif self.state in ['dismissed','corrected'] and has_group_boe:
            corrected_amount = 0
            if self.est_ecart:
                corrected_amount = self.corrected_amount
            vals.update({'state': 'refused','est_ecart':self.est_ecart,'corrected_amount':corrected_amount})
            self.litige_line_id.write(vals)
        else:
            raise ValidationError(_("Vous n'avez pas le droit pour justifier le litige!"))
        return True

class RefuseLitigeLine(models.TransientModel):
    _name = 'refuse.litige.line.wizard'
    _description = 'Detail de litiges refuse'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Many2one('moyen.paiement', string='Mode de paiement', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency)
    montant = fields.Monetary(string='Montant', digits=(12, 3), currency_field='currency_id', required=True)
    motif_id = fields.Many2one('oscar.litige.motif', string="Motif")
    other = fields.Boolean("Autre", related="motif_id.other")
    comment = fields.Text("Commentaire")
    state = fields.Selection([
        ('dismissed', 'Ecarté'),
        ('corrected', 'Corrigé'),
    ], string='Statut', required=True)
    litige_wizard_id = fields.Many2one('refuse.litige.wizard', readonly=True, index=True)
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError

class VerifierPaiement (models.TransientModel):
    _name = 'verifier.paiement.wizard'
    _description = "Verifier paiement Wizard"
    
    def _default_details_ids(self):
        journee_line_id = self._context.get('active_model') == 'oscar.journee.line' and self._context.get('active_id')
        journee_line = self.env['oscar.journee.line'].browse(journee_line_id)
        process_ids = journee_line.mode_other_ids.filtered(lambda m: m.moyen_paiement_id.is_process == True)
        return [
            (0, 0, {'mode_paiement_id': paiement.id ,'process_id': paiement.moyen_paiement_id.id, 'montant': paiement.montant or paiement.montant_gold})
            for paiement in process_ids
        ]

    details_ids = fields.One2many('verifier.paiement.details', 'wizard_id', string='Détails', default=_default_details_ids)
    
    @api.multi
    def deactivate_mode_paiement(self):
        for rec in self.details_ids:
            rec.mode_paiement_id.write({'active':False})
    
    @api.multi
    def confirm_button(self):
        journee_line = self.env['oscar.journee.line'].browse(self._context.get('active_id'))
        espece = 0
        for line in self.details_ids:
            is_refund = False
            num_avoir = ''
            moyen_paiement_id = line.moyen_paiement_id.id
            if line.moyen_paiement_id.code == '0':
                is_refund = True
                if line.num_avoir:
                    num_avoir = line.num_avoir
                else:
                    raise ValidationError("Veuillez saisir le numéro d'avoir !")
                
            if line.moyen_paiement_id.code != '1':
                vals = {'moyen_paiement_id': moyen_paiement_id,
                        'montant': line.montant,
                        'montant_gold': line.montant,
                        'journee_line_id': journee_line.id,
                        'is_refund': is_refund,
                        'user_id':self.env.user.id,
                        'origine_id': line.mode_paiement_id.moyen_paiement_id.id,
                        'num_avoir': num_avoir,
                        'state': 'confirmed',
                    }
                self.env['oscar.mode.paiement'].sudo().create(vals)
            if line.moyen_paiement_id.code == '1':
                espece = espece + line.montant
        journee_line.write({'espece_gold': journee_line.espece_gold + espece, 'check': False})
        self.deactivate_mode_paiement()
        return {'type': 'ir.actions.act_window_close'}
    
class VerifierPaiementDetails (models.TransientModel):
    _name = 'verifier.paiement.details'
    _description = "Verifier paiement Details"
    
    wizard_id = fields.Many2one('verifier.paiement.wizard', string='Wizard', required=True)
    mode_paiement_id = fields.Many2one('oscar.mode.paiement', string="Mode de paiement")
    process_id = fields.Many2one('moyen.paiement', string="Commande")
    montant = fields.Float('Montant', digits=(12,3))
    moyen_paiement_id = fields.Many2one('moyen.paiement', string="Moyen de paiement", domain=lambda self: [('code', 'in', ['0','1','2','3'])] )
    num_avoir = fields.Char(string="Numéro d'avoir")
    
    
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Envelope(models.Model):
    _inherit = "oscar.envelope"
    
    
    journee_ids = fields.One2many('oscar.journee', 'envelope_id', string='Journées', readonly=True, states={'new': [('readonly', False)]})
    journee_content = fields.Boolean(default=False, compute='get_journee_content', store=True)

    @api.constrains('journee_ids','journee_content')
    def _check_journee_ids(self):
        if self.journee_content:
            nbr_jr = len(self.journee_ids.ids)
            if nbr_jr == 0:
                raise ValidationError(_("La liste des journées est vide!"))
            elif nbr_jr > 1:
                raise ValidationError(_("L'enveloppe ne doit contenir qu'une seule journée!"))

    @api.constrains('journee_content','reference_ids')
    def _check_reference_journee(self):
        if self.journee_content:
            count_j = 0
            # count_t = 0
            for ref in self.reference_ids:
                if ref.content_envelope_id.code == 'SAC-JR':
                    count_j = count_j + 1
                    # if ref.ref != ref.ref_confirm:
                    #     raise ValidationError("Les réferences journée ne correspondent pas !")
                # if ref.content_envelope_id.code == 'SAC-TR':
                #     count_t = count_t + 1
                    # if ref.ref != ref.ref_confirm:
                    #     raise ValidationError("Les réferences ticket restaurant ne correspondent pas !")
            if count_j != 1:
                # or count_t != 1
                raise ValidationError(_("Veuillez vérifier Les réferences Sac Journée!"))

    @api.multi
    @api.depends('content_envelope_ids')
    def get_journee_content(self):
        for rec in self:
            if rec.content_envelope_ids:
                    rec.journee_content = False
                    for content in rec.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_journee_id').id:
                            rec.journee_content = True
                            break

    @api.onchange('journee_ids','journee_content')
    def onchange_journee_content(self):
        if self.journee_content == True:
            return {'domain': {'journee_ids': [('state', '=', 'prepared'),('envelope_id', '=', False)]}}
    
    @api.multi
    def envoyer_envelope(self):
        super(Envelope, self).envoyer_envelope()
        for envelope in self:
            if envelope.destinataire_id and self.content_envelope_ids:
                for content in self.content_envelope_ids:
                    if content.id == self.env.ref('spc_transfer_aziza.content_journee_id').id:
                        self.journee_ids.filtered(lambda s: s.state in ['prepared','done1']).write({'state': 'road'})
        return True

    @api.multi
    def recevoir_envelope(self):
        super(Envelope, self).recevoir_envelope()
        for envelope in self:
            if envelope.state == 'receive_warehouse':
                if envelope.content_envelope_ids:
                    for content in envelope.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_journee_id').id:
                            self.journee_ids.filtered(lambda s: s.state == 'road').write({'state': 'done1'})
            if envelope.state == 'receive_siege':
                if envelope.content_envelope_ids:
                    for content in envelope.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_journee_id').id:
                            for journee in envelope.journee_ids:
                                journee.recevoir_journees()

        return True
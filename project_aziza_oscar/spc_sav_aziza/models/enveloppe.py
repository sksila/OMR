# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Envelope(models.Model):
    _inherit = "oscar.envelope"

    # region Fields Declaration
    envelope_claim_ids = fields.Many2many('oscar.sav.claim', 'claim_envelope_rel', 'envelope_id', 'oscar_sav_claim_id'
                                          ,string='Réclamations', readonly=True, states={'new': [('readonly', False)]})
    domain_content = fields.Boolean(default=False, compute='get_name_content', store=True)
    # endregion

    # region Fields methods
    @api.depends('content_envelope_ids')
    def get_name_content(self):
        for rec in self:
            if rec.content_envelope_ids:
                rec.domain_content = False
                for content in rec.content_envelope_ids:
                    if content.id == self.env.ref('spc_transfer_aziza.content_sav_id').id:
                        rec.domain_content = True
    # endregion

    # region Constraints and Onchange
    @api.onchange('envelope_claim_ids','domain_content', 'destinataire_id')
    def envelope_claim_ids_onchange(self):
        if self.destinataire_id.site_type == 'CENTRALE':
            return {'domain': {'envelope_claim_ids': [('state', '=', 'new')]}}
        if self.destinataire_id.site_type == 'MAGASIN':
            return {'domain': {'envelope_claim_ids': [('state', 'in', ['fixed', 'refuse']),('magasin_id', '=', self.destinataire_id.id)]}}


    @api.constrains('envelope_claim_ids')
    def check_claim_in_envelope(self):
        if not self.envelope_claim_ids and self.domain_content:
            raise ValidationError(_("La liste des réclamations est vide!"))
        #parcourir tout les enveloppes déja créer
        enveloppe_obj = self.env['oscar.envelope'].search([('id', '!=', self.id)])
        current_env_obj = self.env['oscar.envelope'].search([('id', '=', self.id)])
        for env in enveloppe_obj:
        #parcourir la liste de reclamation de chaque enveloppe :nommé L1
            for claim_env in env.envelope_claim_ids:
        #si la reclamation choisi existe dans L1
                for current_env in current_env_obj:
                    for claim in current_env.envelope_claim_ids:
                        if claim.id == claim_env.id and claim.state == 'new':
        #alors déclencher l'exception
                            raise ValidationError(_("Cette réclamation existe dans une autre enveloppe"))



    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def envoyer_envelope(self):
        super(Envelope, self).envoyer_envelope()
        for envelope in self:
            if envelope.destinataire_id and self.content_envelope_ids:
                for content in self.content_envelope_ids:
                    if content.id == self.env.ref('spc_transfer_aziza.content_sav_id').id:
                        self.envelope_claim_ids.filtered(lambda s: s.state in ['new','done1']).write({'state': 'road'})
                        self.envelope_claim_ids.filtered(lambda s: s.state in ['done01','fixed','refuse']).write({'state': 'road1'})
        return True

    @api.multi
    def recevoir_envelope(self):
        super(Envelope, self).recevoir_envelope()
        for envelope in self:
            if envelope.state == 'receive_warehouse':
                if self.content_envelope_ids:
                    for content in self.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_sav_id').id:
                            for claim in self.envelope_claim_ids:
                                claim.filtered(lambda s: s.state in ['road']).write({'state': 'done1'})
                                claim.filtered(lambda s: s.state in ['road1']).write({'state': 'done01'})
            if envelope.state == 'receive_siege':
                if self.content_envelope_ids:
                    for content in self.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_sav_id').id:
                            for claim in self.envelope_claim_ids:
                                claim.filtered(lambda s: s.state == 'road').write({'state': 'done2'})
            if envelope.state == 'receive_store':
                if self.content_envelope_ids:
                    for content in self.content_envelope_ids:
                        if content.id == self.env.ref('spc_transfer_aziza.content_sav_id').id:
                            for claim in self.envelope_claim_ids:
                                claim.filtered(lambda s: s.state in ['road1']).write({'state': 'done3'})
        return True
    # endregion

    # region Model methods
    # endregion



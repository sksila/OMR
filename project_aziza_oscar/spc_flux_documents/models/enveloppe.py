# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json


class Enveloppe(models.Model):
    _inherit = "oscar.envelope"
    _description = "Enveloppe"

    # region Fields Declaration

    domain_content_document = fields.Boolean(default=False, compute='get_name_content_document', store=True)
    document_ids = fields.Many2many('ir.attachment', 'attachment_enveloppe_rel', 'enveloppe_id', 'attachment_id'
                                    , string='Documents', readonly=True, states={'new': [('readonly', False)]})

    # endregion

    # region Fields methods
    @api.depends('content_envelope_ids')
    def get_name_content_document(self):
        for rec in self:
            if rec.content_envelope_ids:
                rec.domain_content_document = False
                content_document_id = self.env.ref('spc_transfer_aziza.content_document_id').id
                content_document_rh_id = self.env.ref('spc_transfer_aziza.content_document_rh_id').id
                for content in rec.content_envelope_ids:
                    if content.id in [content_document_id, content_document_rh_id]:
                        rec.domain_content_document = True

    # endregion

    # region Constraints and Onchange
    @api.onchange('document_ids', 'destinataire_id')
    def onchange_destinataire_document(self):
        # récuperer la valeur de destinataire de l'enveloppe et le sauvegarder dans le destinatire de document
        self.document_ids.write({'destinataire_doc_id': self.destinataire_id.id})

    @api.onchange('document_ids', 'domain_content_document', 'content_envelope_ids')
    def envelope_document_ids_onchange(self):
        doc = False
        doc_rh = False
        content_document_id = self.env.ref('spc_transfer_aziza.content_document_id').id
        content_document_rh_id = self.env.ref('spc_transfer_aziza.content_document_rh_id').id
        for content in self.content_envelope_ids:
            if content.id == content_document_id:
                doc = True
            elif content.id == content_document_rh_id:
                doc_rh = True
        if doc:
            return {'domain': {
                'document_ids': [('type_flux', 'in', ['physique', 'binaire']), ('type_doc', '!=', 'rh'), ('enveloppe_id', '=', False),
                                 ('document_type_id', '!=', False), '|', ('state', '=', 'new'),
                                 ('is_uploaded', '=', True)]}}
        elif doc_rh:
            return {'domain': {
                'document_ids': [('type_flux', 'in', ['physique', 'binaire']), ('type_doc', '=', 'rh'),
                                 ('enveloppe_id', '=', False),
                                 ('document_type_id', '!=', False), '|', ('state', '=', 'new'),
                                 ('is_uploaded', '=', True)]}}

    @api.constrains('document_ids', 'domain_content_document')
    def check_document_in_envelope(self):
        # parcourir tout les enveloppes déja créer
        if self.domain_content_document:
            if len(self.document_ids.ids):
                enveloppe_obj = self.env['oscar.envelope'].search([('id', '!=', self.id)])
                current_env_obj = self.env['oscar.envelope'].search([('id', '=', self.id)])
                for env in enveloppe_obj:
                    # parcourir la liste des documents de chaque enveloppe :nommé L1
                    for doc_env in env.document_ids:
                        # si le document choisi existe dans L1
                        for current_env in current_env_obj:
                            for doc in current_env.document_ids:
                                if doc.id == doc_env.id and doc.state == 'new':
                                    # alors déclencher l'exception
                                    raise ValidationError(_("Ce document existe dans un autre enveloppe"))
            else:
                raise ValidationError(_("La liste des documents est vide!"))

    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    @api.multi
    def envoyer_envelope(self):
        super(Enveloppe, self).envoyer_envelope()
        for envelope in self:
            if envelope.destinataire_id and self.content_envelope_ids:
                content_document_id = self.env.ref('spc_transfer_aziza.content_document_id').id
                content_document_rh_id = self.env.ref('spc_transfer_aziza.content_document_rh_id').id
                for content in self.content_envelope_ids:
                    if content.id in [content_document_id, content_document_rh_id]:
                        self.document_ids.filtered(
                            lambda s: s.state in ['new', 'send', 'done1', 'done2', 'done3']).write({'state': 'road'})
        return True

    @api.multi
    def recevoir_envelope(self):
        super(Enveloppe, self).recevoir_envelope()
        content_document_id = self.env.ref('spc_transfer_aziza.content_document_id').id
        content_document_rh_id = self.env.ref('spc_transfer_aziza.content_document_rh_id').id
        for envelope in self:
            if envelope.state == 'receive_warehouse':
                if envelope.content_envelope_ids:
                    for content in envelope.content_envelope_ids:
                        if content.id in [content_document_id, content_document_rh_id]:
                            self.document_ids.filtered(lambda s: s.state == 'road').write({'state': 'done1'})

            if envelope.state == 'receive_siege':
                if envelope.content_envelope_ids:
                    for content in envelope.content_envelope_ids:
                        if content.id in [content_document_id, content_document_rh_id]:
                            envelope.document_ids.filtered(lambda s: s.state == 'road').write({'state': 'done2'})

            if envelope.state == 'receive_store':
                if envelope.content_envelope_ids:
                    for content in envelope.content_envelope_ids:
                        if content.id in [content_document_id, content_document_rh_id]:
                            envelope.document_ids.filtered(lambda s: s.state == 'road').write({'state': 'done3'})
        return True
    # endregion

    # region Model methods
    # endregion

#
# @api.multi
# @api.onchange('type_transfert','destination_id')
# def _select_destination_enveloppe(self):
#     if self.type_transfert=='siege_magasin':
#         self.destination_enveloppe='Siege'
#         self.localisation_enveloppe='Siege'
#     else:
#         for enveloppe in self:
#             if enveloppe.destination_id:
#                 self.destination_enveloppe=enveloppe.destination_id.name
#                 self.localisation_enveloppe=enveloppe.destination_id.name
#
#     @api.multi
#     @api.onchange('type_destination')
#     def _select_destination(self):
#         if self.type_destination=='siege':
#             self.destination=None
#

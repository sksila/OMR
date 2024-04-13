# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _name ='ir.attachment'
    _inherit = ['ir.attachment', 'mail.thread', 'mail.activity.mixin']
    _description = "Documents"
    _mail_post_access = 'read'
    _order = "date_insertion desc"

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ir.attachment.seq')
        if 'numero_piece' in vals:
            vals['numero_piece'] = str(vals['numero_piece']).upper()
        if self.document_type_id.is_fournisseur:
            if not self.fournisseur:
                raise ValidationError('''Vous devez sélectionner un fournisseur !''')
        res = super(IrAttachment, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'numero_piece' in vals:
            vals['numero_piece'] = str(vals['numero_piece']).upper()
        res = super(IrAttachment, self).write(vals)
        for rec in self:
            if rec.document_type_id.is_fournisseur:
                if not rec.fournisseur:
                    raise ValidationError('''Vous devez sélectionner un fournisseur !''')
        return res

    def start_dms_wf(self, vals, wf_name):
        if self.sudo().document_type_id.ws_config_id:
            ws = self.sudo().document_type_id.ws_config_id
            login = ws.ws_login
            password = ws.ws_password
            json_data = json.dumps(vals)
            url = str(ws.ws_url) + str(wf_name)
            try:
                resp = requests.post(url, json_data, auth=(login, password))
            except requests.exceptions.Timeout as e:
                # Maybe set up for a retry, or continue in a retry loop
                _logger.info("Exception Timeout _-_-_ %s" % (e), exc_info=True)
                raise ValidationError(_(e))
            except requests.exceptions.TooManyRedirects as e:
                # Tell the user their URL was bad and try a different one
                _logger.info("Exception TooManyRedirects _-_-_ %s" % (e), exc_info=True)
                raise ValidationError(_(e))
            except requests.exceptions.RequestException as e:
                # catastrophic error. bail.
                _logger.info("Exception RequestException _-_-_ %s" % (e), exc_info=True)
                raise ValidationError(_(e))
        else:
            raise ValidationError(_("Problème de configuration du Web Service, veuillez contacter l'Administrateur!"))
        return resp

    @api.multi
    def send_document(self):
        wf_name = self.document_type_id.wf_ged_id.name
        if not self.datas:
            raise ValidationError(_("Vous devez joindre le document!"))
        if not wf_name:
            raise ValidationError(_("Problème de configuration du Web Service, veuillez contacter l'Administrateur!"))
        numBC = ""
        if len(self.commande_ids.ids) > 0:
            cmd_data = []
            for cmd in self.commande_ids:
                cmd_data.append(str(cmd.name))
            numBC = str(cmd_data).replace('[', '').replace(']', '')
        date_piece = str(self.date_piece) + "T00:00:00Z"
        vals = {"1": {
            "processName": wf_name,
            "signal": "",
            "variables": {
                "typologie": self.document_type_id.code or "Facture",
                "indexOscar": self.name or "",
                "numFacture": self.numero_piece,
                "numBC": numBC,
                "selectSitesBL": self.site_id.code or "",
                "dateFacture": date_piece,
                "montantfacHT": self.total_ht,
                "montantfacTTC": self.total_ttc,
                "commentaire": self.comment or "",
                "cdeFournisseurBL": self.fournisseur.code or "",
                "gedName": self.datas_fname,
                "typFacture": (self.datas).decode('utf-8'),
            }
        }
        }
        resp = self.start_dms_wf(vals, wf_name)
        if resp.status_code == 200:
            _logger.info("Response request_-_-_ %s" % (resp.status_code), exc_info=True)
            self.write({'state': 'send', 'is_uploaded': True})
        else:
            raise ValidationError(_(
                "Problème de configuration du Web Service (%s), veuillez contacter l'Administrateur!" % (
                    resp.status_code)))
        return True

    @api.model
    def _default_source(self):
        current_user = self.env.uid
        sql = ("SELECT s.id FROM public.oscar_site s LEFT JOIN oscar_user_mg_rel rel ON rel.magasin_id = s.id WHERE rel.user_id = %s LIMIT 1;"%(current_user))
        self._cr.execute(sql)
        current_site = self._cr.dictfetchone()
        if current_site:
            return current_site['id']
        return

    @api.multi
    @api.constrains('commande_ids', 'total_ttc', 'total_ht')
    def _check_type_doc(self):
        for doc in self:
            if doc.type_doc in ['facture']:
                if len(doc.commande_ids.ids) == 0:
                    raise ValidationError(_("Veuillez choisir les commandes concernées!"))
                if doc.total_ttc == 0.0 or doc.total_ht == 0.0:
                    raise ValidationError(_("Les totals HT et TTC ne doivent pas être égal à zéro!"))

    name = fields.Char('Index', readonly=True, required=False)
    code = fields.Char('Code', readonly=True)
#     type = fields.Selection([('binary', 'File')],
#                             string='Type', required=True, default='binary', change_default=True,
#                             help="You can either upload a file from your computer or copy/paste an internet link to your file.")
    type_transfert = fields.Selection([
        ('magasin_siege', 'Magasin vers siege'),
        ('siege_magasin', 'Siege vers magasin')], string="Type transfert",compute="_select_destination_document", store=True)
    document_type_id = fields.Many2one('document.type', string='Type du document', index=True)
    date_insertion = fields.Date(string="Date", default=fields.Date.context_today)
    date_piece = fields.Date(string="Date pièce", default=fields.Date.context_today)
    fournisseur = fields.Many2one('res.partner', string="Fournisseur", domain="[('supplier','=',True),('type','=','contact')]", index=True)
    enveloppe_id = fields.Many2one('oscar.envelope', string="Enveloppe", index=True)
    commande_ids = fields.Many2many('commande.gold', 'oscar_cmd_doc_rel', 'doc_id', 'cmd_id', 'Numéro BRV')
    show_document = fields.Boolean("Lié aux commandes GOLD", related='document_type_id.is_document', store=True, index=True)
    comment = fields.Text('Commentaire')
    site_id = fields.Many2one('oscar.site', string="Source", default=_default_source, index=True)
    is_uploaded = fields.Boolean(string="Est envoyé vers la GED")
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('send', 'Envoyé vers la GED'),
        ('road', 'En route'),
        ('done1', 'Reçue à l\'Entrepôt'),
        ('done2', 'Reçue au Siège'),
        ('done3', 'Reçue au Magasin'),
    ], string='Statut', readonly=True, track_visibility='onchange', default="new", index=True)
    user_id = fields.Many2one('res.users', 'Utilisateur', index=True, default=lambda self: self.env.user)
    user_dest_id = fields.Many2one('res.users', string='Destination', index=True, readonly=True)
    libelle_fournisseur = fields.Char(string='Libellé', compute='get_libelle_fournisseur')#, compute='get_libelle_fournisseur'
    numero_piece = fields.Char(string='Numéro pièce', required=False)
    total_ht = fields.Float(string='Total HT', digits=(12, 3))
    total_ttc = fields.Float(string='Total TTC', digits=(12, 3))
    type_flux = fields.Selection([
        ('physique', 'Physique'),
        ('numerique', 'Numérique'),
        ('binaire', 'Physique & Numérique')], string="Type de flux", related="document_type_id.type_flux", store=True)#
    criteres_ids = fields.Many2many('document.criteres', 'document_criteres_rel', 'critere_id', 'attachment_id',
                                    'Critères')
    type_doc = fields.Selection([
        ('facture', 'Facture'),
        ('avoir', 'Avoir'),
        ('bl', 'BL'),
        ('rh', 'RH'),
        ('other', 'Autre')], string="Type Doc", related="document_type_id.type", store=True)
    destinataire_doc_id = fields.Many2one('oscar.site', string="Destinataire document", readonly=True)

    envelope_ids = fields.Many2many('oscar.envelope', 'attachment_enveloppe_rel', 'attachment_id', 'enveloppe_id'
                                    , string='Enveloppes', readonly=True)
    envelope_count = fields.Integer(string='Nombre des enveloppes', compute="_compute_envelope_count")

    @api.one
    @api.depends('envelope_ids')
    def _compute_envelope_count(self):
        self.envelope_count = len(self.envelope_ids.ids)

    @api.one
    @api.depends('type_transfert', 'site_id')
    def _select_destination_document(self):
        for doc in self:
            if doc.site_id:
                if doc.site_id.site_type == 'MAGASIN':
                    self.type_transfert = 'magasin_siege'
                elif doc.site_id.site_type == 'CENTRALE':
                    self.type_transfert = 'siege_magasin'

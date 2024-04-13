# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
import logging

_logger = logging.getLogger(__name__)


class DocumentType(models.Model):
    _name = "document.type"
    _description = "Type Document"

    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    is_document = fields.Boolean("Lié aux commandes GOLD")
    is_fournisseur = fields.Boolean('Le fournisseur est obligatoire pour ce type')
    wf_ged_id = fields.Many2one("document.wf.type", string="Nom de WF")
    type_flux = fields.Selection([
        ('physique', 'Physique'),
        ('numerique', 'Numérique'),
        ('binaire', 'Physique & Numérique')], string="Type de flux", default="physique")
    ws_config_id = fields.Many2one('ws.config', string="Web Service", index=True)
    type = fields.Selection([
        ('facture', 'Facture'),
        ('avoir', 'Avoir'),
        ('bl', 'BL'),
        ('rh', 'RH'),
        ('other', 'Autre')], string="Document", default="other")

    _sql_constraints = [
        ('code_name_uniq', 'UNIQUE (code,name)', 'Le Type Document doit être unique!')
    ]
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
import logging

_logger = logging.getLogger(__name__)


class CommandeGold(models.Model):
    _name = "commande.gold"
    _description = "Commande Gold"

    name = fields.Char('Num Commande', index=True, copy=False,required=True)
    code_site = fields.Char('Code Site')
    lib_site = fields.Char('Site')
    code_fr = fields.Char('Code Fr', index=True)
    lib_fr = fields.Char('Fournisseur')
    date_commande = fields.Date('Date Commande')
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', domain="[('supplier','=',True)]", index=True)
    magasin_id = fields.Many2one('oscar.site', string='Magasin', index=True, domain=[('site_type', '=', 'MAGASIN')])#, default=_default_magasin
    document_ids = fields.Many2many('ir.attachment', 'oscar_cmd_doc_rel', 'cmd_id', 'doc_id', 'Documents')
    active = fields.Boolean(string="Actif", default=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Le numéro de commande doit être unique!')
    ]


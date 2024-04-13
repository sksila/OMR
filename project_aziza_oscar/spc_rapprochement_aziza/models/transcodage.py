# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class Article(models.Model):
    _name = 'transcodage.article'
    _description = 'Transcodage Article'

    name = fields.Char('Désignation')
    code_interne = fields.Char('Code interne', required=True, index=True)
    code_externe = fields.Char('Code externe', required=True, index=True)
    code_fournisseur = fields.Char('Code fournisseur', index=True)


class Site(models.Model):
    _name = 'transcodage.site'
    _description = 'Transcodage Site'

    name = fields.Char('Libellé')
    code_interne = fields.Char('Code interne', required=True, index=True)
    code_externe = fields.Char('Code externe', required=True, index=True)
    code_fournisseur = fields.Char('Code fournisseur', index=True)


class Fournisseur(models.Model):
    _name = 'transcodage.fournisseur'
    _description = 'Transcodage Fournisseur'

    name = fields.Char('Libellé')
    code_interne = fields.Char('Code interne', required=True, index=True)
    code_externe = fields.Char('Code externe', required=True, index=True)

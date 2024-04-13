# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
import logging

_logger = logging.getLogger(__name__)


class WFType(models.Model):
    _name = "document.wf.type"
    _description = "Type WF"
    
    name = fields.Char('Nom', required=True)


class DocumentCriteres(models.Model):
    _name = "document.criteres"
    _description = "Criteres Document"
    
    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    

    
    




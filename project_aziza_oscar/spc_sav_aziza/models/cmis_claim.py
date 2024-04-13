# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.addons.cmis_field import fields
import httplib2
import functools
# 
# # Disable SSL Certificate Validation by python code
httplib2.Http = functools.partial(
    httplib2.Http, disable_ssl_certificate_validation=True)


class SavClaim(models.Model):
    _inherit = 'oscar.sav.claim'

    cmis_folder = fields.CmisFolder(backend_name='Reclamation', string='Réclamation')

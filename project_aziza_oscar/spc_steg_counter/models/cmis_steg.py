# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.addons.cmis_field import fields
from odoo.exceptions import ValidationError
import httplib2
import functools
# 
# # Disable SSL Certificate Validation by python code
httplib2.Http = functools.partial(
    httplib2.Http, disable_ssl_certificate_validation=True)


class CounterReadingSteg(models.Model):
    _inherit = 'oscar.reading.counter.steg'

    cmis_folder = fields.CmisFolder(backend_name='Alfresco', string='Relevé Compteur')

    @api.multi
    def to_validate(self):
        if not self.cmis_folder:
            raise ValidationError(_("Vous devez joindre une photo pour chaque compteur STEG !"))
        return super(CounterReadingSteg, self).to_validate()
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


class AvoirClient(models.Model):
    _inherit = 'oscar.avoir.client'

    cmis_folder = fields.CmisFolder(backend_name='Alfresco', string='Avoir Client')

    # # region Constrains and Onchange
    # @api.constrains('cmis_folder')
    # def _add_piece_jointe(self):
    #     user = self.env.user
    #     if not user.has_group('spc_oscar_aziza.group_reponsable_zone'):
    #         raise ValidationError(_("Vous n'avez pas le permission d'ajouter la pièce jointe!"))

    # endregion
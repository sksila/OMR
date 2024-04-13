# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import tools

class Customer(models.Model):
    _inherit = 'res.partner'


    
    #region Fields declaration
    # is_sav_customer = fields.Boolean('Est un client SAV', default=True)

    @api.multi
    def fixe_error_name(self):
        self.write({'type': False})
        self.write({'type': 'contact'})

    @api.constrains('phone')
    def check_length_phone(self):
        if self.phone:
            if len(self.phone) != 8:
                raise models.ValidationError(_("Un numéro de téléphone mobile est une suite de 8 chiffres."))
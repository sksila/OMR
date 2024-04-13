# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    onlyoffice_host = fields.Char("Host")
    onlyoffice_username = fields.Char("Username")
    onlyoffice_password = fields.Char("Password")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        res.update({
            'onlyoffice_host' : IrConfigPrmtr.get_param('apco.onlyoffice_host'),
            'onlyoffice_username' : IrConfigPrmtr.get_param('apco.onlyoffice_username'),
            'onlyoffice_password' : IrConfigPrmtr.get_param('apco.onlyoffice_password'),
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigPrmtr = self.env['ir.config_parameter'].sudo()
        IrConfigPrmtr.set_param(
            "apco.onlyoffice_host", self.onlyoffice_host
        )
        IrConfigPrmtr.set_param(
            "apco.onlyoffice_username", self.onlyoffice_username
        )
        IrConfigPrmtr.set_param(
            "apco.onlyoffice_password", self.onlyoffice_password
        )
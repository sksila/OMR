# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    endpoint = fields.Char(string='Endpoint')
    label = fields.Char(string='label', config_parameter='spc_sav_aziza.label')
    login = fields.Char(string='login', config_parameter='spc_sav_aziza.login')
    account = fields.Char(string='account', config_parameter='spc_sav_aziza.account')
    password = fields.Char(string='password', config_parameter='spc_sav_aziza.password')
    http_login = fields.Char(string='http login', config_parameter='spc_sav_aziza.http_login')
    http_password = fields.Char(string='http password', config_parameter='spc_sav_aziza.http_password')
    application = fields.Char(string='application', config_parameter='spc_sav_aziza.application')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        endpoint_conf = params.get_param('spc_sav_aziza.endpoint', default=False)
        label_conf = params.get_param('spc_sav_aziza.label', default=False)
        login_conf = params.get_param('spc_sav_aziza.login', default=False)
        account_conf = params.get_param('spc_sav_aziza.account', default=False)
        password_conf = params.get_param('spc_sav_aziza.password', default=False)
        http_login_conf = params.get_param('spc_sav_aziza.http_login', default=False)
        http_password_conf = params.get_param('spc_sav_aziza.http_password', default=False)
        application_conf = params.get_param('spc_sav_aziza.application', default=False)
        res.update(
            endpoint=endpoint_conf,
            label=label_conf,
            login=login_conf,
            account=account_conf,
            password=password_conf,
            http_login=http_login_conf,
            http_password=http_password_conf,
            application=application_conf,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('spc_sav_aziza.endpoint', self.endpoint)
        param.set_param("spc_sav_aziza.label", self.label)
        param.set_param("spc_sav_aziza.login", self.login)
        param.set_param("spc_sav_aziza.account", self.account)
        param.set_param("spc_sav_aziza.password", self.password)
        param.set_param("spc_sav_aziza.http_login", self.http_login)
        param.set_param("spc_sav_aziza.http_password", self.http_password)
        param.set_param("spc_sav_aziza.application", self.application)

# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class WsConfig(models.Model):
    _name = 'ws.config'
    _description = 'Configuration de Web Service'
    
    name = fields.Char(string="Nom", required=True)
    ws_url = fields.Char(string="URL", required=True)
    ws_login = fields.Char(string="Login", required=True)
    ws_password = fields.Char(string="Mot de passe", required=True)
    active = fields.Boolean(string="Actif", default=True)
    params_ids = fields.One2many('ws.params', 'config_id', string='Params')
    

    def _compute_url_with_params(self):
        if len(self.params_ids.ids) > 0 and self.ws_url:
            url = self.ws_url
            url_params = self.ws_url + "?"
            params = []
            for param in self.params_ids:
                if param.type == 'params':
                    params.append(param.name+"="+param.name+"_"+"value")
            if len(params) > 0:
                for param in params:
                    return
                
    
    def _post(self, url, vals, login, password):
        try:
            resp = requests.post(url, json=vals, auth=(login, password))
        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            _logger.info("Exception Timeout _-_-_ %s" %(e), exc_info=True)
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            _logger.info("Exception TooManyRedirects _-_-_ %s" %(e), exc_info=True)
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            _logger.info("Exception RequestException _-_-_ %s" %(e), exc_info=True)
        return resp.status_code
    
    def get_vals(self, obj):
        vals = {}
        print (self.id)
        for param in self.params_ids.filtered(lambda c: c.type == 'Metadata'):
            vals[str(param.name)] = param.field_id.name
        return vals
                    
                

class WsParams(models.Model):
    _name = 'ws.params'
    _description = 'Params de Web Service'
    
    name = fields.Char(string="Key", required=True)
    type = fields.Selection([
        ('params', 'Params'),
        ('metadata', 'Metadata'),
        ], string='Type de données', default='metadata', help='Choisir le type de données', required=True)
    model_id = fields.Many2one('ir.model', string="Modele", index=True, required=True)
    field_id = fields.Many2one('ir.model.fields', string="Value", required=True, index=True)
    config_id = fields.Many2one('ws.config', string="Params", index=True, ondelete='cascade')
    


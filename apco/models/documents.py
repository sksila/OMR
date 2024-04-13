# -*- coding: utf-8 -*-

from curses.ascii import US
from lib2to3.pgen2 import token
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import requests
import json
import os
import base64


class Documents(models.Model):
    _inherit = 'documents.document'
    onlyoffice_id = fields.Integer()

    def open_docs(self):
        if '.doc' in self.name:
            """return {
                'type': 'ir.actions.act_window',
                'name': 'Docs Documents',
                'res_model': 'documents.docs',
                'view_mode': 'form',
            }"""
            return {
                'type': 'ir.actions.act_url',
                'url':  'http://172.104.152.214/example/editor?type=desktop&mode=view&fileName=new.docx'
            }
        elif '.ppt' in self.name:
            return {
                'type': 'ir.actions.act_url',
                'url':  'http://172.104.152.214/example/editor?type=desktop&fileName=sample.pptx'
            }
            """return {
                'type': 'ir.actions.act_window',
                'name': 'PowerPoint Documents',
                'res_model': 'documents.ppt',
                'view_mode': 'form',
            }"""
    
    def open_ppt(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'PowerPoint Documents',
            'res_model': 'documents.ppt',
            'view_mode': 'form',
        }
    def open_in_onlyoffice(self, res_id=None):
        record = self
        if res_id:
            record = self.browse(res_id)
        
        if record.onlyoffice_id > 0:
            host = self.env['ir.config_parameter'].sudo().get_param(
                'apco.onlyoffice_host')
            
            host += '/Products/Files/DocEditor.aspx?fileId=' + str(record.onlyoffice_id)
            return {
                'type': 'ir.actions.act_url',
                'url':  host,
            }

    def get_only_office_url(self, res_id=None):
        record = self
        if res_id:
            record = self.browse(res_id)
        
        if record.onlyoffice_id > 0:
            host = self.env['ir.config_parameter'].sudo().get_param(
                'apco.onlyoffice_host')
            
            host += '/Products/Files/DocEditor.aspx?fileId=' + str(record.onlyoffice_id)
            
            return host
    
    @api.model
    def copy_word(self, folder_id):
        document = self.sudo().search([('name','=','blank.docx'),('active','in',[True,False])],limit=1)
        word_document = document.copy()
        word_document.sudo().write({"datas": document.datas, "mimetype": document.mimetype, "active": True})
        if folder_id:
            word_document.sudo().write({"folder_id": int(folder_id)})
        return word_document.id

    @api.model
    def copy_powerpoint(self, folder_id):
        document = self.sudo().search([('name','=','blank.pptx'),('active','in',[True,False])],limit=1)
        powerpoint_document = document.copy()
        powerpoint_document.sudo().write({"datas": document.datas, "mimetype": document.mimetype, "active": True})
        if folder_id:
            powerpoint_document.sudo().write({"folder_id": int(folder_id)})
        return powerpoint_document.id

    
    def get_access_token(self):
        host = self.env['ir.config_parameter'].sudo().get_param(
            'apco.onlyoffice_host')

        host += '/api/2.0/authentication.json'
        username = self.env['ir.config_parameter'].sudo().get_param(
            'apco.onlyoffice_username')

        password = self.env['ir.config_parameter'].sudo().get_param(
            'apco.onlyoffice_password')
        
        payload = json.dumps({
        "userName": username,
        "password": password
        })
        headers = {
        'Content-Type': 'application/json',
        }

        response = requests.request("POST", host, headers=headers, data=payload)

        if response:
            result = json.loads(response.text)
            return result.get("response").get("token")
        
        return False

    """@api.model
    def create(self, vals):

        record = super().create(vals)
        
        if ".pptx" in record.name or ".PPTX" in record.name or ".docx" in record.name \
            or ".DOCX" in record.name or ".xlsx" in record.name or ".XLSX" in record.name \
                or record.handler == 'spreadsheet':

            token = self.get_access_token()
            if token:

                host = self.env['ir.config_parameter'].sudo().get_param(
                    'apco.onlyoffice_host')
                
                host += "/api/2.0/files/@my/file"

                payload = json.dumps({
                "title": record.name if record.handler != 'spreadsheet' else record.name + ".xlsx"
                })
                headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'Accept': 'application/json',
                }

                response = requests.request("POST", host, headers=headers, data=payload)
                if response:
                    result = json.loads(response.text)
                    record['onlyoffice_id'] = result.get("response").get("id")
        
        return record"""

    @api.model
    def create(self, vals):

        record = super().create(vals)
        
        if ".pptx" in record.name or ".PPTX" in record.name or ".docx" in record.name \
            or ".DOCX" in record.name or ".xlsx" in record.name or ".XLSX" in record.name \
                or record.handler == 'spreadsheet':

            token = self.get_access_token()
            if token:

                host = self.env['ir.config_parameter'].sudo().get_param(
                    'apco.onlyoffice_host')
                
                host += "/api/2.0/files/@my/upload"
                
                payload={}

                
                full_path = record.attachment_id._full_path(record.attachment_id.store_fname)
                    
                file_name = record.name if record.handler != 'spreadsheet' else record.name + ".xlsx"
                files=[
                ('',(file_name,open(full_path, 'rb'),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
                ]

                
                headers = {
                'Authorization': token,
                }
                
                response = requests.request("POST", host, headers=headers, data=payload, files=files)
                print(response.text)
                if response:
                    result = json.loads(response.text)
                    record['onlyoffice_id'] = result.get("response").get("id")
        
        return record

    """This function allow to return the file versions and display it in the log note 
    to have a history for the updates made on the file"""
    def get_file_versions(self, res_id=None):
        record = self
        if res_id:
            record = self.browse(res_id)
        token = self.get_access_token()
        if token:
            baseUrl = self.env['ir.config_parameter'].sudo().get_param(
                'apco.onlyoffice_host')
            fileId = str(record.onlyoffice_id)
            print('fileId: ',fileId)
            url = baseUrl + '/api/2.0/files/file/{}'.format(fileId) + '/history'
            payload = {}
            headers = {
                'Authorization': token,
            }
            response = requests.request("GET", url, headers=headers, params=payload)
            print(response.text)
# -*- coding: utf-8 -*-

from odoo import fields, models, api
import requests
import json
import os


class DocumentsFolder(models.Model):
    _inherit = 'documents.folder'
    partner_id = fields.Many2one('res.partner','Account')
    onlyoffice_id = fields.Integer()


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

    """this function allow to get all the folder informations"""
    def get_folder_information(self):
        token = self.get_access_token()
        if token:
            baseUrl = self.env['ir.config_parameter'].sudo().get_param(
                'apco.onlyoffice_host')
            # how to pass a folder in order to return folder information and the folderId
            folderId = 2689400
            url = baseUrl + '/api/2.0/files/folder/'+ '%s' % (folderId)
            payload = {}
            headers = {
                'Authorization': token,
            }
            response = requests.request("GET", url, headers=headers, params=payload)
            print(response.text)

    """this function allow to create a folder and checking for its existence in the side of onlyoffice"""
    @api.model
    def create(self, vals):
        record = super().create(vals)
        token = self.get_access_token()
        if token:
            baseUrl = self.env['ir.config_parameter'].sudo().get_param(
                'apco.onlyoffice_host')

            # create a non-existing folder:
            # url = baseUrl + '/api/2.0/files/folder/some+text'
            # url = baseUrl + '/api/2.0/files/folder/folderId'
            # create a folder inside an existing folder:
            folderId = 2689400
            url = baseUrl + '/api/2.0/files/folder/' + '%s' % (folderId)
            print(url)
            payload = {'title': record.name}
            # payload = {'folderId': record.parent_folder_id, 'title': str(record.name)}
            print(payload)
            token = self.get_access_token()
            headers = {
                'Authorization': token,
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            print(response.text)

        return record

    # @api.model
    # def create(self, vals):
    #     print('vals: ',vals)
    #     record = super().create(vals)
    #     token = self.get_access_token()
    #     if token:
    #         baseUrl = self.env['ir.config_parameter'].sudo().get_param(
    #             'apco.onlyoffice_host')
    #         # create a non-existing folder:
    #         # url = baseUrl + '/api/2.0/files/folder/some+text'
    #
    #         # create a folder inside an existing folder:
    #         # url = baseUrl + '/api/2.0/files/folder/folderId'
    #         folderId = 2689400
    #         url = baseUrl + '/api/2.0/files/folder/' + '%s' % (folderId)
    #         print(url)
    #         payload = {'title': record.name}
    #         # payload = {'folderId': record.parent_folder_id, 'title': str(record.name)}
    #         print(payload)
    #         headers = {
    #             'Authorization': token,
    #             'Content-Type': 'application/json',
    #             'Accept': 'application/json'
    #         }
    #         # body_data = {'title': record.name}
    #         response = requests.request("POST", url, headers=headers, data=payload)
    #         # response = requests.request("POST", url, headers=headers, data=payload, json=body_data)
    #         print(response.text)
    #         if response:
    #             result = json.loads(response.text)
    #             record['onlyoffice_id'] = result.get("response").get("id")
    #
    #     return record



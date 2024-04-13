# -*- coding: utf-8 -*-

from odoo import api, models, _

from pytz import timezone
from requests import post
from datetime import datetime
from requests.auth import HTTPBasicAuth

NG_TREND_ENCODING_LATIN = 0
NG_TREND_ENCODING_ARABIC = 1
NG_TREND_OPERATION_SEND = 1
NG_TREND_OPERATION_STATUS = 2


class NGTrend(models.TransientModel):
    _name = "spc.sms.ng_trend"

    endpoint = auth = headers = payload = None

    def init(self, http_login=None, http_password=None, account=None, login=None, password=None, application=None,
             label=None, endpoint=None):
        self.endpoint = endpoint
        self.auth = HTTPBasicAuth(http_login, http_password)
        self.headers = {'User-Agent': application, 'Content-type': 'application/x-www-form-urlencoded'}
        self.payload = {'pass': password, 'login': login, 'compte': account, 'label': label}

    def _post(self, data):
        res = post(self.endpoint, auth=self.auth, headers=self.headers, verify=False, data=data)
        return res

    @api.model
    def generate_sms(self, message, destinations, date, reference, encoding=NG_TREND_ENCODING_LATIN,
                     timezone=timezone("Africa/Tunis")):

        params = self.env['ir.config_parameter'].sudo()
        self.init(
            endpoint=params.get_param('spc_sav_aziza.endpoint', None),
            label=params.get_param('spc_sav_aziza.label', None),
            account=params.get_param('spc_sav_aziza.account', None),
            login=params.get_param('spc_sav_aziza.login', None),
            password=params.get_param('spc_sav_aziza.password', None),
            http_login=params.get_param('spc_sav_aziza.http_login', None),
            http_password=params.get_param('spc_sav_aziza.http_password', None),
            application=params.get_param('spc_sav_aziza.application', None)
        )

        if isinstance(destinations, list) and isinstance(date, datetime):
            sms_date = timezone.localize(date)
            return {
                'hr': sms_date.hour,
                'mn': sms_date.minute,
                'dt': sms_date.strftime('%d/%m/%Y'),
                'msg': message,
                'ref': reference,
                'type': encoding,
                'dest_num': destinations
            }
        else:
            raise ValueError(_('Invalid params'))

    @api.model
    def send_message(self, sms):
        self.payload['op'] = NG_TREND_OPERATION_SEND
        payload = self.payload.copy()
        payload.update(sms)
        return self._post(data=payload)

    @api.model
    def sms_status(self, sms):
        self.payload['op'] = NG_TREND_OPERATION_STATUS
        payload = self.payload.copy()
        payload.update(sms)
        return self._post(data=payload)
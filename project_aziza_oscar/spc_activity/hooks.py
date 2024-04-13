# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def uninstall_mail_activity(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    sql_delete_data = """
        DELETE FROM mail_activity;
        """
    env.cr.execute(sql_delete_data)

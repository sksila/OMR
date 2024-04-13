# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard
from .hooks import uninstall_mail_activity


from odoo import api, SUPERUSER_ID

def _auto_post_activity(cr, registry):
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    sql_insert_data = """
    INSERT INTO mail_activity(code,activity_type_id, summary, user_id, date_limite,active) 
    VALUES ('10',1, 'Activity Test', 2, '2020-06-25',False);
    """
    env.cr.execute(sql_insert_data)
    
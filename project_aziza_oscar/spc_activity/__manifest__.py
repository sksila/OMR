# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Planification',
    'version': '12.1',
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 120,
    'summary': 'Permet de planifier les tâches et activités de chaque utilisateur',
    'description': " ",
    'website': 'https://www.spectrumgroupe.fr',
    'depends': [
        'mail',
    ],
    'data': [
        #security
        'security/security_activity.xml',
        'security/ir.model.access.csv',
        'data/alarm_cron.xml',
        'data/alarm_data.xml',
        'data/mail_data.xml',
        'data/activity_cron.xml',
        'data/activity_action_server.xml',

        #wizard
        'wizard/reset_activity_wizard.xml',

        #views
        'views/res_lang_view_inherit.xml',
        'views/mail_activity_views.xml',
        'views/menuitems.xml',
        'views/activity_alarm_views.xml',
        'views/activity_templates.xml',
        'views/mail_activity_type_views.xml',
        'views/mail_tags_views.xml',


    ],
    'demo': [],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'uninstall_hook': 'uninstall_mail_activity',
}

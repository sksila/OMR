# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Planification AZIZA',
    'version': '12.1',
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 120,
    'summary': 'Permet de planifier les tâches et activités de chaque utilisateur',
    'description': " ",
    'website': 'https://www.spectrumgroupe.fr',
    'depends': ['spc_activity', 'spc_oscar_aziza',
    ],
    'data': [
        #security
        'security/security.xml',
        'security/ir.model.access.csv',

        #wizard
        'wizard/import_activities_view.xml',

        #views
        'data/email_template.xml',
        'data/mail_data.xml',
        'views/mail_activity_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
    # 'post_init_hook': '_auto_post_activity',
}

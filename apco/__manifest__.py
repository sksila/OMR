# -*- coding: utf-8 -*-
{
    'name': "APCO",
    'author': "Al Jawad software house",
    'maintainer': 'Al Jawad software house',
    'company': "Al Jawad software house",
    'website': "https://www.al-jawad.ae",


    'category': 'Documents',
    'version': '0.1',


    'depends': ['social','documents_spreadsheet', 'odoo_javascript', 'approvals','planning'],

    'data': [
        'data/approval_category_data.xml',
        'security/groups.xml',
        'views/social.xml',
        'views/documents.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'apco/static/src/**/*.js'
        ],
        'web.assets_qweb': [
            'apco/static/src/xml/*.xml',
        ],
    }
}

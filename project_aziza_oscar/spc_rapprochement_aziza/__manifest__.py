# -*- coding: utf-8 -*-
{
    'name': "Rapprochement",

    'summary': """
         Gestion des bons de réception.
        """,

    'description': """Gestion des rapprochements entre le BRV et BL fournisseur.
    """,
    'sequence': 1,
    'author': "Spectrum groupe",
    'website': "http://www.spectrumgroupe.fr",
    'version': '1.1',
    'category': 'Aziza',
    # any module necessary for this one to work correctly
    'depends': ['spc_oscar_aziza', 'spc_product', 'base_automation'
                ],

    # always loaded
    'data': [
        # security
        'security/rapprochement_security.xml',
        'security/ir.model.access.csv',

        # data
        'data/rapprochement_data.xml',
        'data/automation_data.xml',

        'views/transcodage_views.xml',
        'views/interface_views.xml',
        'views/rapprochement_views.xml',
        'views/oscar_brv_views.xml',
        'views/oscar_bl_views.xml',

    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

# -*- coding: utf-8 -*-
{
    'name': "Web Service - AZIZA",

    'summary': """
        """,

    'description': """
    """,
    'sequence': 1,
    'author': "Spectrum",
    'website': "http://www.spectrumgroupe.fr",
    'version': '12.0.1',
    'category': 'Setting',
    'application': True,
    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/ws_config_views.xml',
    ],
    'application': False,
}
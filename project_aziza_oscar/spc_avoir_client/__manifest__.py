# -*- coding: utf-8 -*-
{
    'name': "Oscar-Avoir Client",

    'summary': """
        Ce module a pour objectif de tracer et de suivre les avoirs clients gérés en magasin.""",

    'description': """
        Ce module a pour objectif de tracer et de suivre les avoirs clients gérés en magasin.
    """,

    'author': "Spectrum Groupe",
    'website': "https://www.spectrumgroupe.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Aziza',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'spc_oscar_aziza',
                'cmis_field',
    ],

    # always loaded
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'data/sequence_avoir_client.xml',
        'views/avoir_client_views.xml',
        'views/cmis_avoir_client_views.xml',
        'views/validation_rz_avoir.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
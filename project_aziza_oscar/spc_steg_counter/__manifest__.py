# -*- coding: utf-8 -*-
{
    'name': "Relevé des Compteurs STEG",

    'summary': """
        Valorisation de la consommation énergétique""",

    'description': """
        Ce module a pour objectif de suivre la consommation réelle d’énergie (en KWH) de chaque magasin et de simplifier 
        et de fiabiliser la consolidation des résultats et la valorisation de la consommation énergétique.
    """,

    'author': "Spectrum Groupe",
    'website': "https://www.spectrumgroupe.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Spectrum',
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
        'data/sequence_reading_counter.xml',
        'views/counter_views.xml',
        'views/reading_counter_views.xml',
        'views/cmis_reading_counter_views.xml',
        'views/oscar_site_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# -*- coding: utf-8 -*-
{
    'name': "SPEC Utils",

    'summary': """
        Collection of utils components
    """,

    'description': """
        Contains custom reusable components (Fields, Widgets,...)
    """,

    'author': "Dridi <mohamed.elfateh.dridi@spectrumgroupe.fr>",
    'website': "https://spectrumgroupe.fr",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    'external_dependencies': {
        "python": [],
        "lib": []
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/assets.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}

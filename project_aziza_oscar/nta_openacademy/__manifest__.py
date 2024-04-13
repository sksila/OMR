{
    'name': "openacademy",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/course_manager_security.xml',
        'security/ir.model.access.csv',
        'data/res_partner_demo.xml',
        'data/course_demo.xml',
        'data/session_demo.xml',
        'views/openacademy_views.xml',
        'views/course_views.xml',
        'views/session_views.xml',
        'views/partner_views.xml',
        # 'views/session_board_views.xml',
        'wizard/session_add_attendees_views.xml',
        'report/session_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True
}
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Oscar Administration',
    'version': '1.1',
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 1,
    'summary': 'Gestion des sites (Magasin, Entrepôt...)',
    'description': "Gérer les sites (Magasin, Entrepôt), les clients, les fournisseurs, les articles, les employées",
    'website': 'https://www.spectrumgroupe.fr',
    'depends': [
       'base',
       'dynamic_uid',
       'product',
       'hr',
        'fleet',
       'muk_web_theme',
#        'odoo_web_login',
       'spec_utils',
    ],
    'data': [
        #security
        'security/oscar_aziza_security.xml',
        'security/ir.model.access.csv',

        'data/site_inter_cron.xml',
        #views
        'views/oscar_templates.xml',
        'views/menus_view.xml',
        'views/res_users_views.xml',
        'views/res_bank_views.xml',
        'views/customer_view.xml',
        'views/supplier_view.xml',
        'views/employee_view.xml',
        'views/oscar_site_view.xml',
        'views/driver_views.xml',
        'views/ir_cron_views.xml',
        'views/oscar_inter_site.xml',
        'views/oscar_inter_employee_views.xml',
    ],
    'demo': [],
    'qweb': ['static/src/xml/base.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

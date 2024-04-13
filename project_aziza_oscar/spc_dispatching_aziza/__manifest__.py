# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Oscar-Gestion de dispatching',
    'version': '1.1',
    'author': "Spectrum Groupe",
    'category': 'Retour',
    'sequence': 1,
    'summary': 'Gestion de dispatching',
    'description': """
    Gérer les demandes de dispatching et maîtriser les stocks dormants et des surstocks
    """,
    'website': '',
    'depends': [
        'base',
        'spc_oscar_aziza',
        'spc_product',
        'mail',
    ],
    'data': [
            'security/dispatching_security.xml',
            'security/ir.model.access.csv',
            'data/dispatching_data.xml',
            'data/template_notif_by_email.xml',
            'wizard/wizard_rejet_views.xml',
            'wizard/wizard_confirmation.xml',

            'views/users_view.xml',
            'views/dispatch_reset_views.xml',
            'views/dispatching_views.xml',
            'views/dispatching_lines_details_verifications_views.xml',
            'views/category_views.xml',
            'views/motif_view.xml',
#             'views/spot_view.xml',
            'views/product_view.xml',

    ],
    'application': True,
}

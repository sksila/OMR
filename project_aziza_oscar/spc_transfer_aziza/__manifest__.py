# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Oscar Transfert',
    'version': '1.1',
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 1,
    'summary': 'Gestion des enveloppes AZIZA',
    'description': "Un module de gestion des enveloppes et bordereaux dédié à AZIZA",
    'website': 'https://www.spectrumgroupe.fr',
    'depends': [
        'fleet',
        'spc_oscar_aziza',
    ],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/transfer_security.xml',
        'data/transfer_data.xml',

        # wizard
        'wizard/change_source_wizard.xml',

        # report QWEB
        'report/enveloppe_report.xml',
        'report/bordereau_report.xml',

        # views
        'views/menus_view.xml',
        'views/vehicle_view.xml',
        'views/enveloppe_view.xml',
        'views/bordereau_views.xml',
        'views/envelope_content_views.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

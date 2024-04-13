# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Flux de documents ',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 1,
    'author': "Spectrum groupe",
    'summary': 'Flux de documents',
    'description': """
Manage aziza 
=========================================
This application allows you to manage document of aziza 


    """,
    'website': '',
    'depends': [
        'mail',
        'base',
        'spc_oscar_aziza',
        'spc_ws_aziza',
        'spc_transfer_aziza',
    ],
    'version': '12.0.1',
    'data': [
            'data/flux_documents_data.xml',
            'data/attachment_sequence.xml',
            'security/flux_documents_security.xml',
            'security/ir.model.access.csv',

            'report/document_enveloppe_report.xml',

            'views/flux_document_menuitem.xml',
            'views/ir_attachment_views.xml',
            'views/document_type_views.xml',
            'views/document_wf_type_views.xml',
            'views/commande_gold_view.xml',
            'views/criteres_views.xml',
            'views/bordereau_views.xml',
            'views/enveloppe_views.xml',
            # 'report/report_bon_envoie.xml',
            'views/commande_gold_view.xml',
            'views/inter_commande_view.xml',
    ],
    'application': True,
}

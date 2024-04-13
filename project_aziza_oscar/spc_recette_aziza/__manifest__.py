# -*- coding: utf-8 -*-
{
    'name': "Flux financier",
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 1,
    'summary': 'Gestion des recettes magasin AZIZA',
    'description': '''Gérer facilement les recettes des magsins AZIZA:
        - Gestion des journées
        - Gestion des écarts
        - Gestion des litiges 
        - Gestion des borderaux
        - Gestion des droits d'accès
    ''',
    'website': 'https://www.spectrumgroupe.fr',
    # any module necessary for this one to work correctly
    'depends': [
       'base',
       'dynamic_uid',
       'spc_oscar_aziza',
       'spc_transfer_aziza',
       'cmis_field'
    ],
    # always loaded
    'data' : [
        #security
        'security/recette_security.xml',
        'security/ir.model.access.csv',
        #data
        'data/recette_data.xml',
        'data/recette_action.xml',
        
        'views/menu_views.xml',
        #wizard
        'wizard/mg_cron_wizard_views.xml',
        'wizard/not_up_journee_wizard_views.xml',
        'wizard/verifier_paiement_wizard_view.xml',
        'wizard/change_state_journee_wizard.xml',
        'wizard/refuse_litige_wizard.xml',

        #views
        'views/res_partner_view.xml',
        'views/journee_views.xml',
        'views/journee_recue_views.xml',
        'views/ecart_view.xml',
        'views/versement_views.xml',
        'views/dispatching_views.xml',
        'views/ir_cron_views.xml',
        'views/enveloppe_view.xml',
        'views/oscar_report.xml',
        'views/report_versement.xml',
        'views/report_versement_cheque.xml',
        'views/report_ecarts.xml',
        'views/gold_journee_views.xml',
         
        'report/journee_report_views.xml',
        'report/journee_enveloppe_report.xml',

        'views/versement_cmis_views.xml',
        'views/ecart_cmis_views.xml'
        ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
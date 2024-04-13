# -*- coding: utf-8 -*-
{
    'name': "Oscar SAV Aziza",

    'summary': """
         Service après-vente.
        """,

    'description': """Gérer les réclamations des clients
    """,
    'sequence': 1,
    'author': "Spectrum groupe",
    'website': "http://www.spectrumgroupe.fr",
    'version': '1.1',
    'category': 'Aziza',
    # any module necessary for this one to work correctly
    'depends': ['spc_oscar_aziza',
                'spc_transfer_aziza',
                'cmis_field',
                ],

    # always loaded
    'data': [
        'security/sav_security.xml',
        'security/ir.model.access.csv',
        
        'data/sav_data.xml',

        'views/report_bon_sortie.xml',
        
        'wizard/bon_sortie_wizard_views.xml',
        'wizard/article_modif_wizard_views.xml',

        'report/sav_enveloppe_report.xml',
        'report/avoir_or_echange_mail_template.xml',
        
        'views/claim_views.xml',
        'views/cmis_claim_views.xml',
        'views/product_views.xml',
        'views/envelope_view.xml',
        'views/sav_report.xml',
        'views/report_claim.xml',
        'views/problem_views.xml',
        'views/res_config_settings_views.xml',
        'views/customer_views.xml',
        'report/claim_report_views.xml',
        'report/sav_bordereau_report.xml'
    ],
   'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

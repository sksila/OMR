# -*- coding: utf-8 -*-

{
    'name': "Oscar Contrat Aziza",

    'summary': """
         Gestion des contrats.
        """,

    'description': """
    Ce module permet la gestion des contrats avec des fonctions d'évaluation période d'essai des employés. 
    Vous pouvez également imprimer le rapport de contrat.
    """,
    'sequence': 1,
    'author': "Spectrum groupe",
    'website': "http://www.spectrumgroupe.fr",
    'version': '1.1',
    'category': 'Sale',
    # any module necessary for this one to work correctly
    'depends': ['base','hr_contract','spc_oscar_aziza'],

    # always loaded
    'data': [
        'security/contract_security.xml',
        'security/ir.model.access.csv',
        'data/contract_data.xml',
        'wizard/wizard_import_excel_views.xml',
        
        'views/renewal_contract_views.xml',
        'views/evaluation_views.xml',
        
        'views/contract_report.xml',
        'views/report_evaluation.xml',
        'views/report_renouvellement.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
  }
{
    'name': 'Survey Aziza : Clean survey',
    'author': 'Spectrum Groupe',
    'category': 'Aziza',
    'sequence': 8,
    'website': 'https://www.spectrumgroupe.fr',
    # any module necessary for this one to work correctly
    'depends': [
       'survey',
       'spc_survey',
       'spc_survey_extra',
       'spc_product',
       'spc_oscar_aziza',
       'website_replace_header_footer'
    ],
    # always loaded
    'data' : [
        #data
        'data/survey_type.xml',
        'data/views.xml',
        #security
        'security/rules.xml',
        'security/ir.model.access.csv',
        #views
        'views/survey_page_inherit.xml',
        'views/objectifs.xml',
        'views/survey_question_inherit.xml',
        'views/survey_templates_inherit.xml',
        'views/tempates.xml',
        'views/plano_facing_site.xml',
        'views/site_inherit.xml'
        ],
    'installable': True,
    'application': True,
    'auto_install': False,

}


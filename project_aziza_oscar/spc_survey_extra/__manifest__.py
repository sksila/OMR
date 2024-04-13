{
    'name': 'Spectrum survey extra',
    'author': 'Spectrum Groupe',
    'category': 'Spectrum',
    'sequence': 9,
    'summary': 'survey extra module',
    'description': 'add auto-fill feature in advanced matrix type',
    'website': 'https://www.spectrumgroupe.fr',
    # any module necessary for this one to work correctly
    'depends': [
        'spc_survey',
    ],
    # always loaded
    'data': [
        'views/assets.xml',
        # security
        'security/ir.model.access.csv',
        # data
        # wizard
        'wizard/row_columns_display.xml',
        'wizard/column_dependency_help.xml',
        'wizard/syntax.xml',
        # views
        'views/survey_templates_inherit.xml',
        'views/control_m_1.xml',
        'views/survey_survey_inherit.xml',
        'views/survey_label_inherit.xml',
        'views/question_display.xml',
        'views/column_dependency.xml',
        'views/survey_question_inherit.xml',
        'views/criteria_type.xml',
        'views/scoring_inherit.xml',
        'views/survey_page_inherit.xml',

        'report/report_page_inherit.xml',
        'report/report_session_inherit.xml'
    ],
    'external_dependencies' : {
        'python' : ['mechanize'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

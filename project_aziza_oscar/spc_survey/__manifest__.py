{
    'name': 'Spectrum survey',
    'author': 'Spectrum Groupe',
    'category': 'Spectrum',
    'sequence': 2,
    'summary': 'This is a survey module made by Spectrum groupe',
    'description': '',
    'website': 'https://www.spectrumgroupe.fr',
    # any module necessary for this one to work correctly
    'depends': [
        'survey',
        'website_survey',
        'dynamic_uid',
        'web_widget_many2many_tags_multi_selection',
        'mail',
        'spc_planning_aziza'
    ],
    # always loaded
    'data': [
        'views/assets.xml',
        'views/inherit_survey_js_templates.xml',
        'report/report_layout.xml',
        # security
        'security/spc_survey_security.xml',
        'security/ir.model.access.csv',
        # data
        'data/audit_activity.xml',
        'data/res_company.xml',
        'data/survey_data.xml',
        'data/survey_stages.xml',
        # wizard
        'wizard/page_final_score.xml',
        'wizard/session_final_score.xml',
        # views
        'views/views.xml',
        'views/res_config_settings_views.xml',
        'views/report_structure.xml',
        'views/survey_session.xml',
        'views/survey_templates_inherit.xml',
        'views/scoring.xml',
        'views/survey_label_inherit.xml',
        'views/survey_question_inherit.xml',
        'views/survey_page_inherit.xml',
        'views/survey_survey_inherit.xml',
        'views/survey_user_input_line_inherit.xml',
        'views/survey_type.xml',
        'views/survey_user_input_inherit.xml',
        'report/report_page.xml',
        'report/report_session.xml',
        'views/mail_activity.xml',
        'report/report_final_only_anomalies.xml',
        'report/mail_template.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

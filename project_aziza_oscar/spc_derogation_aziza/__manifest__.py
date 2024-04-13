# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Oscar-Gestion de derogation',
    'version': '1.1',
    'author': 'Spectrum Groupe',
    'category': 'Retour',
    'sequence': 1,
    'summary': 'Gestion de derogation',
    'description': """
    Gestion des articles à DLV proche ou exiprée, articles non-conformes et objet de retrait
    """,
    'website': '',
    'depends': [
        'base',
        'spc_oscar_aziza',
        'mail',
        # --- External --- #
        'report_xlsx',
    ],
    'data': [
        'security/derogation_security.xml',
        'security/ir.model.access.csv',

        'data/derogation_data.xml',
        'data/mail_template_data.xml',
        'data/cron_magasin.xml',
        'data/template_notif_by_email.xml',

        'wizard/wizard_rejet_views.xml',
        'wizard/wizard_comment_views.xml',
        'wizard/wizard_comment_magasin_views.xml',

        'report/derogation_menu_report.xml',

        'views/res_lang_view_inherit.xml',
        'views/derogation_views.xml',
        'views/category_views.xml',
        'views/derogation_exploitation_groupe_view.xml',
        'views/derogation_magasin_groupe_view.xml',
        'views/derogation_approvisonneur_groupe_view.xml',
        'views/derogation_marchandise_groupe_view.xml',
        'views/derogation_quality_group_view.xml',
        'views/derogation_cg_groupe_views.xml',
        'views/derogation_dg_groupe_views.xml',
        'views/derogation_line.xml',

        'wizard/wizard_add_quantity.xml',
        'wizard/add_quantity_magasin.xml',
        'wizard/wizard_confirmation.xml',

    ],
    'application': True,
}

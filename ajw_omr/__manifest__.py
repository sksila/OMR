# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Optical Mark Recognition-v2',
    'version' : '1.1',
    'summary': '',
    'sequence': 100,
    'description': """
    With this module, teachers will spend nearly one minute checking all of their students' answers with a high correct rate of over 99.9 percent,
    and this project will analyze and summarize all important information about wrong or right answers, which difficult questions have a high error rate.
    """,
    'category': 'Accounting/Accounting',
    'website': 'https://www.al-jawad.ae',
    'images' : [],
    'depends' : ['base','survey'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/grading.csv',
        'views/survey_views.xml',
        # 'views/student_info.xml',
        # 'views/grading_views.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

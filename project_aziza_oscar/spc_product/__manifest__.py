{
    'name': 'Aziza product',
    'author': 'Spectrum Groupe',
    'category': 'Spectrum',
    'sequence': 2,
    'summary': 'This is a survey module made by Spectrum groupe',
    'description': '',
    'website': 'https://www.spectrumgroupe.fr',
    # any module necessary for this one to work correctly
    'depends': [
        'spc_oscar_aziza',
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/spc_product_type_data.xml',
        'data/cron.xml',
        'views/product_type.xml',
        'views/product_inherit.xml',
        'views/interfacage.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

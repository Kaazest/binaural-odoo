# -*- coding: utf-8 -*-
{
    'name': "Inventory Alerts",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Aarón",
    'website': "",

    'category': 'Inventory',
    'version': '17.0.0.1',

    'depends': ['base', 'stock', 'sale_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

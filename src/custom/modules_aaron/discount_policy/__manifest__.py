{
    'name': "Discount Policy",
    'summary': """
        Gestión de políticas de descuentos.
    """,
    'description': """
        Módulo para estructurar y aplicar políticas de descuento avanzadas.
    """,
    'author': "Aaron",
    'website': "",
    'category': 'Sales',
    'version': '17.0.0.1',
    'depends': ['base', 'sale', 'contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/discount_policy_views.xml',
        'views/client_type_views.xml',
        'views/res_partner_views.xml',
        'data/client_type_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

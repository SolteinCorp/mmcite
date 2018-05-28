{
    'name': "eCommerce - Cotización en Línea",
    'summary': """
        Soportar la cotización en línea de los productos.
    """,

    'description': "",

    'author': "Armando Robert Lobo <arobertlobo5@gmail.com> (SOLTEIN SA. DE CV.)",
    'website': "http://www.soltein.net",

    'category': 'Website',
    'version': '0.1',

    'depends': [
        'website', 
        'crm', 
        'sale_management', 
        'website_sale',
        'website_sale_options'
    ],

    'data': [
        'data/data.xml',

        'views/templates.xml',
        'views/product_template_views.xml',
    ],

    'installable': True,
    'application': True,
}
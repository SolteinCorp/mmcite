# -*- coding: utf-8 -*-
{
    'name': "MMCITÉ",

    'summary': """
        Características adicionales solicitadas por BKT/MMCITE.""",

    'description': """
        Se implementan un grupo de adecuaciones necesarias para cumplir con las expectativas de 
        BKT/MMCITÉ relativas a la adopción de Odoo como portal empresarial y como ERP.

        Mejoras incluidas:

        #. Opción de Cotización desde el Sito Web.
        #. Otros requisitos solicitados.

    """,

    'author': "Armando Robert Lobo <arobertlobo5@gmail.com> (SOLTEIN SA. DE CV.)",
    'website': "http://www.soltein.net",

    'category': 'MMCITE',
    'version': '0.1',

    'depends': ['website_sale_basket_crm'],

    'data': [
        'data/data.xml',
        'security/user_groups.xml',
        'report/sale_report_template.xml',
        'views/crm_lead_views.xml',
        'views/templates.xml',
    ],

    'installable': True,
    'application': True,
}
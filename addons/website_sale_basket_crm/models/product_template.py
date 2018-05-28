# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    related_product_ids = fields.Many2many(
        string="Related Products",
        comodel_name="product.template",
        relation="product_related_product_rel",
        column1="product_id",
        column2="related_product_id",
        help="Products related to other products.",
    )

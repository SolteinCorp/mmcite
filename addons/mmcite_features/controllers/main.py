# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.addons.website_sale_basket_crm.controllers.main import WebsiteSaleBasketCrm

class MMCITEFeatures(WebsiteSaleBasketCrm):
    def get_quotation_form_values(self, **kwargs):
        values = super(MMCITEFeatures, self).get_quotation_form_values(**kwargs)
        values.update({
            'project_name': kwargs.get('project', "")
        })
        return values

    # Firewall
    def shop(self, **post):
        raise NotFound()
    
    def product(self, **post):
        raise NotFound()

    def pricelist(self, **post):
        raise NotFound()

    def pricelist_change(self, **post):
        raise NotFound()

    def cart(self, **post):
        raise NotFound()

    def cart_update(self, **post):
        raise NotFound()

    def cart_update_json(self, **post):
        raise NotFound()

    def address(self, **post):
        raise NotFound()

    def checkout(self, **post):
        raise NotFound()

    def confirm_order(self, **post):
        raise NotFound()

    def extra_info(self, **post):
        raise NotFound()

    def payment(self, **post):
        raise NotFound()

    def payment_transaction(self, **post):
        raise NotFound()

    def payment_token(self, **post):
        raise NotFound()

    def payment_get_status(self, **post):
        raise NotFound()

    def payment_validate(self, **post):
        raise NotFound()

    def terms(self, **post):
        raise NotFound()

    def payment_confirmation(self, **post):
        raise NotFound()

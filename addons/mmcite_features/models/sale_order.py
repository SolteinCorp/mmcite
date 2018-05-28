# -*- encoding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, values):
        res = super(SaleOrder, self).create(values)
        try:
            opportunity = res.opportunity_id
            if opportunity.exists():
                if len(opportunity.order_ids) <= 1:
                    opportunity.planned_revenue = res.amount_total   
        except AttributeError:
            pass

        return res
    
    @api.multi
    def write(self, values):        
        res = super(SaleOrder, self).write(values)
        for order in self:
            try:
                opportunity = order.opportunity_id
                if opportunity.exists():
                    if len(opportunity.order_ids) <= 1:
                        opportunity.planned_revenue = order.amount_total   
            except AttributeError:
                pass

        return res

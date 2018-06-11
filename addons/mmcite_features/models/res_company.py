# -*- encoding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def set_external_report_layout(self):
        self.env.ref('base.main_company').external_report_layout = 'standard'
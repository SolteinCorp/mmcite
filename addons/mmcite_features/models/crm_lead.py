# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    project_name = fields.Char(
        help="The project name for current opportunity. Use in negotiation process."
    )

    lead_city_name = fields.Char(
        string="City Name",
        help="Oportunity city name."
    )

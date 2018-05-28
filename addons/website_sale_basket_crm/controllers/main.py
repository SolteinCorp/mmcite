# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.http_routing.models.ir_http import slug

from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale_options.controllers.main import WebsiteSale

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

_logger = logging.getLogger(__name__)


class WebsiteSaleBasketCrm(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, is_sale_basket_crm=False):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        else: 
            if is_sale_basket_crm:
                domain += [('public_categ_ids', '=', False)]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

    @http.route(['/products/cart/update_option'], type='http', auth="public", methods=['POST'], website=True, multilang=True)
    def products_cart_options_update_json(self, **kw):
        if 'lang' in kw.keys():
            request.website = request.website.with_context(lang=kw.get('lang'))

        order = request.website.sale_get_order(force_create=1)

        products = []
        attributes = self._filter_attributes(**kw)

        for k, v in kw.items():
            if 'add_qty_' in k:
                products.append((int(k.lstrip('add_qty_')), int(v), ))

        for product_id, add_qty in products:
            product = request.env['product.product'].browse(int(product_id))
            option_ids = product.optional_product_ids.mapped('product_variant_ids').ids

            optional_product_ids = []
            for k, v in kw.items():
                if "optional-product-" in k and int(kw.get(k.replace("product", "add"))) and int(v) in option_ids:
                    optional_product_ids.append(int(v))

            if add_qty > 0:
                value = order._cart_update(
                    product_id=int(product_id),
                    add_qty=add_qty,
                    attributes=attributes,
                    optional_product_ids=optional_product_ids
                )

            for option_id in optional_product_ids:
                order._cart_update(
                    product_id=option_id,
                    set_qty=value.get('quantity'),
                    attributes=attributes,
                    linked_line_id=value.get('line_id')
                )
        
        return str(order.cart_quantity)

    @http.route([
        '/products',
        '/products/page/<int:page>',
        '/products/category/<model("product.public.category"):category>',
        '/products/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True, multilang=True)
    def products(self, page=0, category=None, search='', ppg=False, **post):
        if 'lang' in post.keys():
            request.website = request.website.with_context(lang=post.get('lang'))
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if category:
            category = request.env['product.public.category'].search([('id', '=', int(category))], limit=1)
            if not category:
                raise NotFound()

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values, is_sale_basket_crm=True)

        keep = QueryURL(
            '/products', 
            category=category and int(category), 
            search=search, 
            attrib=attrib_list, 
            order=post.get('order')
        )

        compute_currency, pricelist_context, pricelist = self._get_compute_currency_and_context()

        request.context = dict(
            request.context, 
            pricelist=pricelist.id, 
            partner=request.env.user.partner_id
        )

        url = "/products"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        categs = request.env['product.public.category'].search([('parent_id', '=', False)])
        Product = request.env['product.template']

        parent_category_ids = []
        parent_categories = []
        if category:
            url = "/products/category/%s" % slug(category)
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_categories = [current_category.parent_id] + parent_categories 
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        product_count = Product.search_count(domain)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            selected_products = Product.search(domain, limit=False)
            attributes = ProductAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        values = {
            'slug': slug,
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'parent_category_ids': parent_category_ids,

            # Extra
            'is_sale_basket_crm': True,
            'parent_categories': parent_categories,
            '_': _
        }
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)

    @http.route([
        '/products/product/<model("product.template"):product>',
    ], type='http', auth="public", multilang=True, website=True)
    def products_product(self, product, category='', search='', **kwargs):
        if 'lang' in kwargs.keys():
            request.website = request.website.with_context(lang=kwargs.get('lang'))
        product_context = dict(request.env.context,
                               active_id=product.id,
                               partner=request.env.user.partner_id)
        ProductCategory = request.env['product.public.category']
        parent_categories = []

        if category:
            current_category = ProductCategory.browse(int(category))
            category = current_category.exists()
            if category:
                parent_categories = [current_category]
                while current_category.parent_id:
                    parent_categories = [current_category.parent_id] + parent_categories 
                    current_category = current_category.parent_id

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/products', category=category and category.id, search=search, attrib=attrib_list)

        categs = ProductCategory.search([('parent_id', '=', False)])

        pricelist = request.website.get_current_pricelist()

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: from_currency.compute(price, to_currency)

        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)

        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids,            
            # Extra
            'is_sale_basket_crm': True,
            'parent_categories': parent_categories,
            '_': _
        }
        return request.render("website_sale.product", values)
    
    @http.route(['/products/cart'], type='http', auth="public", website=True, multilang=True)
    def products_cart(self, access_token=None, revive='', **post):
        """
        Main cart management + abandoned cart revival
        access_token: Abandoned cart SO access token
        revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
        """
        if 'lang' in post.keys():
            request.website = request.website.with_context(lang=post.get('lang'))

        order = request.website.sale_get_order()
        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:  # wrong token (or SO has been deleted)
                return request.render('website.404')
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session['sale_order_id']):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/products/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session['sale_order_id']:  # abandoned cart found, user have to choose what to do
                values.update({'access_token': abandoned_order.access_token})

        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: from_currency.compute(price, to_currency)
        else:
            compute_currency = lambda price: price

        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
            'suggested_products': [],

            # Extra
            'is_sale_basket_crm': True,
            '_': _
        })
        if order:
            _order = order
            if not request.env.context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("website_sale.cart", values)

    @http.route(['/products/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False, multilang=True)
    def products_cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        if 'lang' in kw.keys():
            request.website = request.website.with_context(lang=kw.get('lang'))

        request.website.sale_get_order(force_create=1)._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            attributes=self._filter_attributes(**kw),
        )
        return request.redirect("/products/cart")

    @http.route(['/products/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False, multilang=True)
    def products_cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kwargs):
        if 'lang' in kwargs.keys():
            request.website = request.website.with_context(lang=kwargs.get('lang'))
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        value = order._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)

        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity
        from_currency = order.company_id.currency_id
        to_currency = order.pricelist_id.currency_id

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'compute_currency': lambda price: from_currency.compute(price, to_currency),
            'suggested_products': order._cart_accessories(),

            # Extra
            'is_sale_basket_crm': True,
            '_': _
        })
        return value

    @http.route(['/shop/get_unit_price'], type='json', auth="public", methods=['POST'], website=True, multilang=True)
    def get_unit_price(self, product_ids, add_qty, **kw):
        if 'lang' in kw.keys():
            request.website = request.website.with_context(lang=kw.get('lang'))
        products = request.env['product.product'].with_context({'quantity': add_qty}).browse(product_ids)
        return {product.id: product.website_price / (add_qty if add_qty != 0 else 1) for product in products}


    @http.route(['/products/modal'], type='json', auth="public", methods=['POST'], website=True, multilang=True)
    def products_modal(self, product_id, **kw):
        if 'lang' in kw.keys():
            request.website = request.website.with_context(lang=kw.get('lang'))

        pricelist = request.website.get_current_pricelist()
        product_context = dict(request.context)
        quantity = kw['kwargs']['context']['quantity']
        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
        # fetch quantity from custom context
        product_context.update(kw.get('kwargs', {}).get('context', {}))

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: request.env['res.currency']._compute(from_currency, to_currency, price)
        product = request.env['product.product'].with_context(product_context).browse(int(product_id))

        products = []
        main_product_attr_ids = self.get_attribute_value_ids(product)
        
        for variant in main_product_attr_ids:
            products.append(dict(
                product_id=variant[0],
                product=request.env['product.product'].with_context(product_context).browse(int(variant[0])),
                attributes=variant 
            ))
            if variant[0] == product.id:
                # We indeed need a list of lists (even with only 1 element)
                main_attr_ids = [variant]

        return request.env['ir.ui.view'].render_template("website_sale_options.modal", {
            'product': product,
            'quantity': quantity,
            'compute_currency': compute_currency,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'main_product_attr_ids': main_attr_ids,

            # Extra
            'is_sale_basket_crm': True,
            'products': products,
            '_': _
        })

    @http.route(['/products/partner'], type='http', auth="public", methods=['GET', 'POST'], website=True, multilang=True)
    def products_partner(self, **kwargs):
        if 'lang' in kwargs.keys():
            request.website = request.website.with_context(lang=kwargs.get('lang'))

        order = request.website.sale_get_order()
        if not order.exists() or not order.order_line.exists():
            request.redirect('/products')

        PUBLIC_USER = request.env.ref('base.public_user')
        user = request.env.user
        if PUBLIC_USER != user:
            partner = user.partner_id
        else:
            partner = request.env['res.partner']

        values = {
            'is_sale_basket_crm': True,
            'tag_ids': request.env['crm.lead.tag'].sudo().search([]),
            'partner': partner,
            'lead': order.opportunity_id or request.env['crm.lead'].sudo(),
            'request': request,

            # Extra
            '_': _
        }
        
        return request.render('website_sale_basket_crm.partner', values)

    def get_quotation_form_values(self, **kwargs):
        order = request.website.sale_get_order()
        values = {
            'contact_name': kwargs.get('contact_name'),
            'type': 'opportunity',
            'name': _("New Quotation by %s") % kwargs.get('contact_name', _("Unknown...")),
            'email_from': kwargs.get('email_from'),
            'phone': kwargs.get('phone'),
            'partner_name': kwargs.get('partner_name'),
            'description': kwargs.get('description'),
            'planned_revenue': order.amount_total,
            'order_ids': [(6, None, [order.id])],
            'tag_ids': [(6, None, [int(tag) for tag in kwargs.get('tag_ids', []).split(',')])],
            'team_id': request.env.ref('sales_team.salesteam_website_sales').id,
            'medium_id': request.env.ref('utm.utm_medium_website').id
        }
        return values

    @http.route(['/products/quotation'], type="http", method=['POST'], auth="public", website=True, multilang=True)
    def products_quotation(self, **kwargs):
        if 'lang' in kwargs.keys():
            request.website = request.website.with_context(lang=kwargs.get('lang'))

        order = request.website.sale_get_order()
        if not order.exists() or not order.order_line.exists():
            request.redirect('/products')
        if len(kwargs.keys()) < 5:
            request.redirect('/products')

        values = self.get_quotation_form_values(**kwargs)
        
        lead = order.opportunity_id.sudo()
        if lead.exists():
            lead.write(values)
        else:
            lead = request.env['crm.lead'].sudo().create(values)
            order.write({
                'opportunity_id': lead.id,
                'tag_ids': [(6, None, map(int, kwargs.get('tag_ids', []).split(',')))],
                'team_id': request.env.ref('sales_team.salesteam_website_sales').id,
                'medium_id': request.env.ref('utm.utm_medium_website').id
            })

        if kwargs.get('return_basket', 'false') == 'true':
            return json.dumps({
                "success": True,
                "redirect": "/products/cart"
            })
        else:
            request.website.sale_reset()
            order.state = 'sent'
            
            lead.write({
                'team_id': order.team_id.id,
            })

        return json.dumps({
            "success": True,
            "redirect": "/products/quotation/success"
        })

    @http.route(['/products/quotation/success'], type="http", method=['GET'], auth="public", website=True, multilang=True)
    def products_quotation_success(self, **kwargs):
        if 'lang' in kwargs.keys():
            request.website = request.website.with_context(lang=kwargs.get('lang'))
        return request.render('website_sale_basket_crm.quotation_success', {})

    @http.route(['/products/print'], type='http', auth="public", website=True)
    def products_print_saleorder(self):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            pdf, _ = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([sale_order_id])
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return request.redirect('/products')
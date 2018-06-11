odoo.define('website_sale_basket_crm.website_sale', function(require) {
"use strict";
    require('web.dom_ready');

    var core = require('web.core');
    var weContext = require("web_editor.context");
    var ajax = require('web.ajax');
    var _t = core._t, _lt = core._lt;

    
    var shopping_cart_link = $('ul#top_menu li a[href$="/products/cart"]');
    var shopping_cart_link_counter;

    shopping_cart_link.popover({
        trigger: 'manual',
        animation: true,
        html: true,
        title: function () {
            return _t("My Cart");
        },
        container: 'body',
        placement: 'auto',
        template: '<div class="popover mycart-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
    }).on("mouseenter",function () {
        var self = this;
        clearTimeout(shopping_cart_link_counter);
        shopping_cart_link.not(self).popover('hide');
        shopping_cart_link_counter = setTimeout(function(){
            if($(self).is(':hover') && !$(".mycart-popover:visible").length)
            {
                $.get("/products/cart", {'type': 'popover'})
                    .then(function (data) {
                        $(self).data("bs.popover").options.content =  data;
                        $(self).popover("show");
                        $(".popover").on("mouseleave", function () {
                            $(self).trigger('mouseleave');
                        });
                    });
            }
        }, 100);
    }).on("mouseleave", function () {
        var self = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                if(!$(self).is(':hover')) {
                    $(self).popover('hide');
                }
            }
        }, 1000);
    });

    $('.oe_website_sale #add_to_cart, .oe_website_sale #products_grid .a-submit')
        .off('click')
        .removeClass('a-submit')
        .click(function (event) {
            var $form = $(this).closest('form');
            var quantity = parseFloat($form.find('input[name="add_qty"]').val() || 0);
            var product_id = parseInt($form.find('input[type="hidden"][name="product_id"], input[type="radio"][name="product_id"]:checked').first().val(),10);
            var is_sale_basket_crm = $(this).data('is-sale-basket-crm');        
            event.preventDefault();
            ajax.jsonRpc(
                is_sale_basket_crm ? "/products/modal" : "/shop/modal", 
                'call', {
                    'product_id': product_id,
                    'kwargs': {
                    'context': _.extend({'quantity': quantity}, weContext.get())
                    },
                }).then(function (modal) {
                    var $modal = $(modal);

                    $modal.find('img:first').attr("src", "/web/image/product.product/" + product_id + "/image_medium");

                    // disable opacity on the <form> if currently active (in case the product is
                    // not published), as it interferes with bs modals
                    $form.addClass('css_options');

                    $modal.appendTo($form)
                        .modal()
                        .on('hidden.bs.modal', function () {
                            $form.removeClass('css_options'); // possibly reactivate opacity (see above)
                            $(this).remove();
                        });

                    $modal.on('click', '.a-submit', function (ev) {
                        var $a = $(this);
                        $form.ajaxSubmit({
                            url:  is_sale_basket_crm ? "/products/cart/update_option" : "/shop/cart/update_option",
                            data: {lang: weContext.get().lang},
                            success: function (quantity) {
                                if (!$a.hasClass('js_goto_shop')) {
                                    window.location.pathname = window.location.pathname.replace(/products([\/?].*)?$/, is_sale_basket_crm ? "products/cart" :  "shop/cart");
                                }
                                var $q = $(".my_cart_quantity");
                                $q.parent().parent().removeClass("hidden", !quantity);
                                $q.html(quantity).hide().fadeIn(600);
                            }
                        });
                        $modal.modal('hide');
                        ev.preventDefault();
                    });

                    $modal.on('click', '.css_attribute_color input', function (event) {
                        $modal.find('.css_attribute_color').removeClass("active");
                        $modal.find('.css_attribute_color:has(input:checked)').addClass("active");
                    });

                    $modal.on("click", "a.js_add, a.js_remove", function (event) {
                        event.preventDefault();
                        var $parent = $(this).parents('.js_product:first');
                        $parent.find("a.js_add, span.js_remove").toggleClass("hidden");
                        $parent.find("input.js_optional_same_quantity").val( $(this).hasClass("js_add") ? 1 : 0 );
                        $parent.find(".js_remove");
                    });

                    $modal.on("change", "input.js_quantity", function () {
                        var qty = parseFloat($(this).val());
                        if (qty === 1) {
                            $(".js_remove .js_items").addClass("hidden");
                            $(".js_remove .js_item").removeClass("hidden");
                        } else {
                            $(".js_remove .js_items").removeClass("hidden").text($(".js_remove .js_items:first").text().replace(/[0-9.,]+/, qty));
                            $(".js_remove .js_item").addClass("hidden");
                        }
                    });

                    $modal.find('input[name="add_qty"]').val(quantity).change();
                    $('.js_add_cart_variants').each(function () {
                        $('input.js_variant_change, select.js_variant_change', this).first().trigger('change');
                    });

                    $modal.on("change", 'input[name="add_qty"]', function (event) {
                        var product_id = $($modal.find('span.oe_price[data-product-id]')).first().data('product-id');
                        var product_ids = [product_id];
                        var $products_dom = [];
                        $("ul.js_add_cart_variants[data-attribute_value_ids]").each(function(){
                            var $el = $(this);
                            $products_dom.push($el);
                            _.each($el.data("attribute_value_ids"), function (values) {
                                product_ids.push(values[0]);
                            });
                        });
                    });
                });
            return false;
        });

    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;

        var clickwatch = (function(){
            var timer = 0;
            return function(callback, ms){
              clearTimeout(timer);
              timer = setTimeout(callback, ms);
            };
        })();

        $(oe_website_sale).off(
            "change", ".oe_cart input.js_quantity[data-product-id]"
        ).on("change", ".oe_cart input.js_quantity[data-product-id]", function () {
            var $input = $(this);
            if ($input.data('update_change')) {
                return;
            }
            var is_sale_basket_crm = $input.data('is-sale-basket-crm');            
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var $dom = $(this).closest('tr');
            //var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'),10);
            var product_ids = [parseInt($input.data('product-id'),10)];
            clickwatch(function(){
              $dom_optional.each(function(){
                  $(this).find('.js_quantity').text(value);
                  product_ids.push($(this).find('span[data-product-id]').data('product-id'));
              });
              $input.data('update_change', true);
  
              ajax.jsonRpc(is_sale_basket_crm ? "/products/cart/update_json" : "/shop/cart/update_json", 'call', {
                  'line_id': line_id,
                  'product_id': parseInt($input.data('product-id'), 10),
                  'set_qty': value
              }).then(function (data) {
                  $input.data('update_change', false);
                  var check_value = parseInt($input.val() || 0, 10);
                  if (isNaN(check_value)) {
                      check_value = 1;
                  }
                  if (value !== check_value) {
                      $input.trigger('change');
                      return;
                  }
                  var $q = $(".my_cart_quantity");
                  if (data.cart_quantity) {
                      $q.parents('li:first').removeClass("hidden");
                      $('#get_partner_data').show();
                  }
                  else {
                      $q.parents('li:first').addClass("hidden");
                      $('a[href*="/shop/checkout"]').addClass("hidden");
                      $('#get_partner_data').hide();
                  }
  
                  $q.html(data.cart_quantity).hide().fadeIn(600);
                  $input.val(data.quantity);
                  $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
  
                  $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
  
                  if (data.warning) {
                      var cart_alert = $('.oe_cart').parent().find('#data_warning');
                      if (cart_alert.length === 0) {
                          $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
                                  '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                      }
                      else {
                          cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                      }
                      $input.val(data.quantity);
                  }
              });
            }, 500);
        });
    });

    // Partner Form
    var select = $('select.js_select2');
    select.select2({
        tokenSeparators: [',']
    });
    select.on('change', function() {
        $(this).trigger('blur');
        $("input[name='tag_ids']").val(select.val());
    });

    $.validator.addMethod("mobileMX", function(value, element) {
        return this.optional( element ) || /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/.test( value );
    }, "Please specify a valid mobile number" );

    var validations = {
        ignore: '.select2-input, .select2-focusser',
        rules: {
            contact_name: {
                required: true,
                minWords: 2
            },
            email_from: {
                required: true
            },
            description:  {
                required: true,
            }            
        },
        messages: {
            // TODO: Problema no identificado con la internalización de los mensajes
            contact_name: {
                //required: _lt("Your name are required!"),
                required: "¡Su nombre y al menos un apellido son requeridos!",
                //minWords: _lt("Please at least name and surename.")
                minWords: "¡Nombre y al menos el primer apellido!"
            },
            email_from: {
                //required: _lt("An email to contact is required!"),
                required: "¡Se requiere un correo para contactarle!",
                //email: _lt("Please enter a valid email address."),
                email: "¡Se requiere una dirección de correo válida!"
            },
            description: {
                required: "¡Su mensaje es requerido, por favor cuéntenos sus motivos y necesidades!",
            }             
        },
        errorElement: 'small',
        errorPlacement: function (error, element) {
            // Add the `help-block` class to the error element
            error.addClass("help-block");

            // Add `has-feedback` class to the parent div.form-group
            // in order to add icons to inputs
            element.parents(".form-group").addClass("has-feedback");
            
            // Append error
            error.appendTo(element.parents(".form-group"));

            // Add the span element, if doesn't exists, and apply the icon classes to it.
            if (!element.next("span")[0]) {
                $( "<span class='glyphicon glyphicon-remove form-control-feedback'></span>" ).insertAfter( element );
            }
        },
        success: function (label, element) {
            // Add the span element, if doesn't exists, and apply the icon classes to it.
            if (!$(element).next("span")[0] ) {
                $( "<span class='glyphicon glyphicon-ok form-control-feedback'></span>" ).insertAfter($(element));
            }
        },
        highlight: function ( element, errorClass, validClass ) {
            $(element).parents(".form-group" ).addClass("has-error").removeClass("has-success");
            $(element).next("span").addClass("glyphicon-remove").removeClass("glyphicon-ok");
        },
        unhighlight: function ( element, errorClass, validClass ) {
            $(element).parents(".form-group").addClass("has-success").removeClass("has-error");
            $(element).next("span").addClass("glyphicon-ok").removeClass("glyphicon-remove");
        }
    };

    $('#contact').validate(validations);

    $('.request_quotation, .return_basket').off('click').on('click', function() {
        var button = $(this),
            data_form = button.closest("form");
        if (data_form.valid()) {
            data_form.ajaxSubmit({
                url:  "/products/quotation",
                method: 'POST',
                data: {
                    lang: weContext.get().lang,
                    return_basket: button.hasClass("return_basket")
                },
                success: function (data) {
                    console.debug(data);
                    data = JSON.parse(data);
                    console.debug(data);
                    if (data.redirect) {
                        window.location.replace(data.redirect);
                    }
                }
            });
        }              
    });

    $('#privacy_check').change(function(e){
        var check = $(this),
            send_quotation = $('#send_quotation').prop('disabled', !check.prop('checked'));
    });
});



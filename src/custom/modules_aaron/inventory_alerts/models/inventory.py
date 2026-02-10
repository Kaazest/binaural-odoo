# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import Markup

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)

        for move in self:
            if move.product_id.detailed_type == 'product':
                product = move.product_id
                
                #Validación 
                if product.minimal_stock > 0 and product.qty_available < product.minimal_stock:
                    
                    msg = Markup(
                        f"<b>ALERTA DE STOCK BAJO</b><br/>"
                        f"El producto <a href='#' data-oe-model='product.product' data-oe-id='{product.id}'>{product.name}</a> "
                        f"ha quedado con stock <b>{product.qty_available}</b> "
                        f"(Mínimo: {product.minimal_stock})."
                    )

                    self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                        'type': 'warning',
                        'title': "Stock Mínimo Alcanzado",
                        'message': f"El producto {product.name} ha bajado de su stock mínimo ({product.minimal_stock}). Actual: {product.qty_available}",
                        'sticky': False,
                    })

                    if move.picking_id:
                        move.picking_id.message_post(
                            body=msg,
                            subject="Alerta de Stock Mínimo",
                            message_type='comment',
                            subtype_xmlid='mail.mt_note'
                        )
                    
                    product.sudo().message_post(
                        body=msg,
                        subject="Alerta de Stock Mínimo",
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )

                    product.product_tmpl_id.sudo().message_post(
                        body=msg,
                        subject="Alerta de Stock Mínimo",
                        message_type='comment',
                        subtype_xmlid='mail.mt_note'
                    )

        return res
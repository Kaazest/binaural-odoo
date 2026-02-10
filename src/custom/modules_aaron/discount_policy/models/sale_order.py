from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_discount_policy(self):
        # Recalcular descuentos si cambia el cliente
        for line in self.order_line:
            line._onchange_discount_policy()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_discount_policy(self):
        """
        Aplica automáticamente el descuento al cambiar producto o cantidad.
        """
        if not self.product_id or not self.order_id.partner_id:
            return

        DiscountRule = self.env['discount.policy.rule']
        best_discount = DiscountRule.get_best_discount(self.order_id.partner_id, self.product_id, self.product_uom_qty)
        
        # Aplicamos siempre el descuento calculado por la política.
        # Esto permite que si el nuevo cliente/cantidad no tiene descuento (0.0),
        # se elimine el descuento anterior (se "limpie").
        if self.discount != best_discount:
            self.discount = best_discount

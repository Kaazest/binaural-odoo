from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        # Aplicar descuentos antes de postear la factura
        for move in self:
            if move.move_type in ('out_invoice', 'out_receipt'):
                move._apply_discount_policy()
        
        return super(AccountMove, self).action_post()

    def _apply_discount_policy(self):
        """
        Itera sobre las líneas de la factura y aplica la mejor regla de descuento encontrada.
        Uses the centralized logic in discount.policy.rule.
        """
        self.ensure_one()
        DiscountRule = self.env['discount.policy.rule']
        
        for line in self.invoice_line_ids:
            if not line.product_id:
                continue

            best_discount = DiscountRule.get_best_discount(self.partner_id, line.product_id, line.quantity)
            
            # Solo aplicamos si es mejor que el actual.
            if best_discount > line.discount:
                line.write({'discount': best_discount})

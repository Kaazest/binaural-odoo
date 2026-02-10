from odoo import models, fields, api

class DiscountPolicyRule(models.Model):
    _name = 'discount.policy.rule'
    _description = 'Reglas de Descuentos'
    _order = 'min_quantity'

    policy_id = fields.Many2one('discount.policy', string="Política Padre", ondelete='cascade')
    
    # Criterios de Aplicación
    client_type_id = fields.Many2one('res.client.type', string="Tipo de Cliente")
    product_id = fields.Many2one('product.product', string="Producto")
    category_id = fields.Many2one('product.category', string="Categoría de Producto")
    
    # Condición
    min_quantity = fields.Float(string="Cantidad Mínima", default=1.0)
    
    # Beneficio
    discount_percentage = fields.Float(string="Porcentaje de Descuento (%)", required=True)

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        for record in self:
            if record.discount_percentage < 0 or record.discount_percentage > 100:
                raise models.ValidationError("El porcentaje de descuento debe estar entre 0 y 100.")

    @api.model
    def get_best_discount(self, partner, product, quantity):
        """
        Calcula el mejor descuento aplicable según las reglas definidas.
        :param partner: Recordset de res.partner
        :param product: Recordset de product.product
        :param quantity: Cantidad float
        :return: Porcentaje de descuento (float)
        """
        if not product:
            return 0.0

        domain = [
            ('policy_id.active', '=', True),
            ('min_quantity', '<=', quantity),
        ]
        
        # Condición OR para Client Type: es el del cliente O es False (para todos)
        if partner.client_type_id:
            domain += ['|', ('client_type_id', '=', False), ('client_type_id', '=', partner.client_type_id.id)]
        else:
             domain += [('client_type_id', '=', False)]

        # Condición OR para Producto
        domain += ['|', ('product_id', '=', False), ('product_id', '=', product.id)]
        
        # Condición OR para Categoría
        domain += ['|', ('category_id', '=', False), ('category_id', '=', product.categ_id.id)]
        
        # Buscamos la regla que ofrezca el mayor descuento
        rule = self.search(domain, order='discount_percentage desc', limit=1)
        
        return rule.discount_percentage if rule else 0.0

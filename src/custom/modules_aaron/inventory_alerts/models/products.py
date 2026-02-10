from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    minimal_stock = fields.Float(string="Stock Mínimo", default=0.0)
    
    is_low_stock = fields.Boolean(
        string="Stock Crítico", 
        compute='_compute_is_low_stock', 
        search='_search_is_low_stock'
    )

    @api.depends('qty_available', 'minimal_stock')
    def _compute_is_low_stock(self):
        for record in self:
            if record.minimal_stock > 0 and record.qty_available < record.minimal_stock:
                record.is_low_stock = True
            else:
                record.is_low_stock = False

    def _search_is_low_stock(self, operator, value):
        if operator == '=' and value:
            products = self.search([('minimal_stock', '>', 0)])
            alerts = products.filtered(lambda p: p.qty_available < p.minimal_stock)
            return [('id', 'in', alerts.ids)]
        return []
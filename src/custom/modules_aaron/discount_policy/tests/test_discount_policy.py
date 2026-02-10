from odoo.tests import common, Form
from odoo.exceptions import ValidationError

class TestDiscountPolicy(common.TransactionCase):

    def setUp(self):
        super(TestDiscountPolicy, self).setUp()
        
        # Datos base
        self.Product = self.env['product.product']
        self.Partner = self.env['res.partner']
        self.DiscountPolicy = self.env['discount.policy']
        self.DiscountRule = self.env['discount.policy.rule']
        self.ClientType = self.env['res.client.type']
        self.AccountMove = self.env['account.move']
        self.SaleOrder = self.env['sale.order']

        # Productos
        self.product_a = self.Product.create({'name': 'Producto A', 'list_price': 100})
        self.product_b = self.Product.create({'name': 'Producto B', 'list_price': 200})
        
        # Tipos de Cliente
        self.type_retail = self.ClientType.create({'name': 'Minorista Test'})
        self.type_wholesale = self.ClientType.create({'name': 'Mayorista Test'})
        
        # Clientes
        self.partner_retail = self.Partner.create({'name': 'Cliente Minorista', 'client_type_id': self.type_retail.id})
        self.partner_wholesale = self.Partner.create({'name': 'Cliente Mayorista', 'client_type_id': self.type_wholesale.id})
        self.partner_none = self.Partner.create({'name': 'Cliente Sin Tipo'})
        
        # Política General Activa
        self.policy = self.DiscountPolicy.create({'name': 'Política General', 'active': True})
        
        # Regla 1: Minorista, Prod A, Qty >= 10 -> 10%
        self.DiscountRule.create({
            'policy_id': self.policy.id,
            'client_type_id': self.type_retail.id,
            'product_id': self.product_a.id,
            'min_quantity': 10,
            'discount_percentage': 10.0
        })
        
        # Regla 2: Mayorista, Prod A, Qty >= 5 -> 20%
        self.DiscountRule.create({
            'policy_id': self.policy.id,
            'client_type_id': self.type_wholesale.id,
            'product_id': self.product_a.id,
            'min_quantity': 5,
            'discount_percentage': 20.0
        })
        
        # Regla 3: Todos (Sin cliente), Prod B, Qty >= 1 -> 5%
        self.DiscountRule.create({
            'policy_id': self.policy.id,
            'product_id': self.product_b.id,
            'min_quantity': 1,
            'discount_percentage': 5.0
        })

    def create_invoice(self, partner, lines_data):
        invoice_lines = []
        for product, qty in lines_data:
            invoice_lines.append((0, 0, {
                'product_id': product.id,
                'quantity': qty,
                'price_unit': product.list_price,
            }))
            
        invoice = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': invoice_lines,
        })
        return invoice

    def test_01_no_discount_insufficient_qty(self):
        """ Caso 1: Cliente Minorista compra 5 unidades de A (Min es 10). No aplica descuento. """
        invoice = self.create_invoice(self.partner_retail, [(self.product_a, 5)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.discount, 0.0, "No se debería aplicar descuento (cantidad insuficiente)")

    def test_02_discount_retail_success(self):
        """ Caso 2: Cliente Minorista compra 10 unidades de A. Aplica 10%. """
        invoice = self.create_invoice(self.partner_retail, [(self.product_a, 10)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.discount, 10.0, "Se debería aplicar 10% de descuento para minorista")

    def test_03_discount_wholesale_success(self):
        """ Caso 3: Cliente Mayorista compra 5 unidades de A. Aplica 20%. """
        invoice = self.create_invoice(self.partner_wholesale, [(self.product_a, 5)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.discount, 20.0, "Se debería aplicar 20% de descuento para mayorista")

    def test_04_generic_rule_success(self):
        """ Caso 4: Cliente sin tipo específico compra Prod B. Aplica regla general de 5%. """
        invoice = self.create_invoice(self.partner_none, [(self.product_b, 1)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_b)
        self.assertEqual(line.discount, 5.0, "Se debería aplicar 5% de descuento por regla general")

    def test_05_best_discount_selection(self):
        """ Caso 5: Múltiples reglas aplicables, debe elegir la mejor (mayor porcentaje). """
        # Creamos una regla adicional para Producto B con mayor descuento si compra más de 10
        self.DiscountRule.create({
            'policy_id': self.policy.id,
            'product_id': self.product_b.id,
            'min_quantity': 10,
            'discount_percentage': 15.0
        })
        
        # Compra 12 unidades (Aplica regla de 5% y regla de 15%).
        invoice = self.create_invoice(self.partner_none, [(self.product_b, 12)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_b)
        self.assertEqual(line.discount, 15.0, "Se debería aplicar el mejor descuento disponible (15%)")

    def test_06_policy_inactive(self):
        """ Caso 6: Si la política está inactiva, no se aplica ningun descuento. """
        self.policy.active = False
        invoice = self.create_invoice(self.partner_retail, [(self.product_a, 10)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.discount, 0.0, "No se debería aplicar descuento si la política está inactiva")

    def test_07_client_type_mismatch(self):
        """ Caso 7: Cliente Minorista intenta usar regla de Mayorista (comprando 5 unids). """
        # Regla Mayorista: min 5 -> 20%. Regla Minorista: min 10 -> 10%.
        # Compra 5 unidades. Como Minorista necesita 10, no aplica la suya.
        # Y no debe aplicar la de Mayorista aunque cumpla la cantidad.
        invoice = self.create_invoice(self.partner_retail, [(self.product_a, 5)])
        invoice.action_post()
        
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.discount, 0.0, "No se debería aplicar regla de Mayorista a Minorista")

    def test_08_sale_order_onchange_customer(self):
        """ Caso 8: Cambiar cliente en Sale Order actualiza el descuento. """
        
        # 1. Crear SO directamente
        so = self.SaleOrder.create({
            'partner_id': self.partner_wholesale.id,
            'order_line': [(0, 0, {
                'product_id': self.product_a.id,
                'product_uom_qty': 5,
                'price_unit': 100
            })]
        })
        
        # Simular onchange de quantity/product al crear
        for line in so.order_line:
            line._onchange_discount_policy()
            
        line = so.order_line[0]
        # Mayorista con 5 units -> 20%
        self.assertEqual(line.discount, 20.0, "Inicialmente debería ser 20% pa Mayorista")
        
        # 2. Cambiar a cliente Minorista (que con 5 unidades NO tiene descuento por min 10)
        so.partner_id = self.partner_retail.id
        so._onchange_partner_discount_policy() # Simular el onchange de partner
        
        self.assertEqual(line.discount, 0.0, "Al cambiar a Minorista (5 unids), descuento debe bajar a 0% (req 10)")
        
        # 3. Aumentar cantidad a 10 para Minorista
        line.product_uom_qty = 10
        line._onchange_discount_policy() # Simular onchange quantity
        
        self.assertEqual(line.discount, 10.0, "Con 10 unids, Minorista recibe 10%")
        
        # 4. Cambiar a cliente Sin Tipo (Regla general no aplica a Prod A, solo B)
        so.partner_id = self.partner_none.id
        so._onchange_partner_discount_policy()
        
        self.assertEqual(line.discount, 0.0, "Cliente sin tipo no tiene descuento para Prod A")


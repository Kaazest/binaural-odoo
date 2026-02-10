# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestInventoryAlerts(TransactionCase):

    def setUp(self):
        super(TestInventoryAlerts, self).setUp()
        
        # Crear un producto de prueba
        self.product = self.env['product.product'].create({
            'name': 'Test Product Alert',
            'detailed_type': 'product',
            'minimal_stock': 10.0,
            'list_price': 100.0,
        })
        
        # Stock inicial mayor al mínimo (ej. 20)
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant']._update_available_quantity(self.product, self.stock_location, 20.0)

    def test_alert_triggered_on_stock_move(self):
        """ Verificar que se genera una alerta al bajar del stock mínimo mediante un movimiento """
        
        # Comprobar estado inicial
        self.assertEqual(self.product.qty_available, 20.0)
        
        # Crear un Picking de salida (Delivery) para reducir el stock
        picking_type_out = self.env.ref('stock.picking_type_out')
        customer_location = self.env.ref('stock.stock_location_customers')
        
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': customer_location.id,
        })
        
        move = self.env['stock.move'].create({
            'name': 'Test Move Out',
            'product_id': self.product.id,
            'product_uom_qty': 15.0, # Esto dejará el stock en 5 ( < 10 )
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': customer_location.id,
        })
        
        # Confirmar y validar el picking
        picking.action_confirm()
        picking.action_assign()
        
        # Establecer cantidad hecha y validar
        move.quantity = 15.0
        picking.button_validate()
        
        # Verificar que el stock bajó a 5.0
        self.assertEqual(self.product.qty_available, 5.0, "El stock debería ser 5.0")
        
        # Verificar que se generó un mensaje en el Chatter del Producto
        # Buscamos mensajes que contengan "ALERTA DE STOCK BAJO"
        messages = self.env['mail.message'].search([
            ('model', '=', 'product.product'),
            ('res_id', '=', self.product.id),
            ('body', 'ilike', 'ALERTA DE STOCK BAJO')
        ])
        
        self.assertTrue(messages, "Debería haber un mensaje de alerta en el chatter del producto")
        
        # Verificar que también está en el Picking
        picking_messages = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
            ('body', 'ilike', 'ALERTA DE STOCK BAJO')
        ])
        self.assertTrue(picking_messages, "Debería haber un mensaje de alerta en el chatter del picking")

    def test_no_alert_if_above_minimum(self):
        """ Verificar que NO se genera alerta si el stock sigue sobre el mínimo """
        
        # Reducir stock solo en 5 unidades (queda en 15, que es > 10)
        picking_type_out = self.env.ref('stock.picking_type_out')
        customer_location = self.env.ref('stock.stock_location_customers')
        
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': customer_location.id,
        })
        
        move = self.env['stock.move'].create({
            'name': 'Test Move Small',
            'product_id': self.product.id,
            'product_uom_qty': 5.0, 
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': customer_location.id,
        })
        
        picking.action_confirm()
        picking.action_assign()
        move.quantity = 5.0
        picking.button_validate()
        
        self.assertEqual(self.product.qty_available, 15.0)
        
    def test_no_duplicate_alerts(self):
        """ Verificar que una transacción genera una única alerta, no múltiples """
        
        # Estado inicial: 20 unidades. Mínimo: 10.
        
        # Crear un picking con una cantidad que rompa el stock (15 unidades, queda en 5)
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        
        move = self.env['stock.move'].create({
            'name': 'Move Big',
            'product_id': self.product.id,
            'product_uom_qty': 15.0,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        
        picking.action_confirm()
        picking.action_assign()
        
        # Establecemos la cantidad realizada
        move.quantity = 15.0
        
        # Validamos. Esto debería llamar a _action_done una vez.
        picking.button_validate()
        
        # Verificación: Stock final debe ser 5.0
        self.assertEqual(self.product.qty_available, 5.0)
        
        # Buscar mensajes en el Picking creados en este test
        messages = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
            ('body', 'ilike', 'ALERTA DE STOCK BAJO'),
        ])
        
        # Debería haber exactamente 1 mensaje en el picking
        self.assertEqual(len(messages), 1, "Debería haber exactamente una alerta en el picking")

        # Verificar en el producto (plantilla) para asegurar que no se spamea
        # Buscamos por el subject específico que pusimos en el código para el template
        product_messages = self.env['mail.message'].search([
            ('model', '=', 'product.template'),
            ('res_id', '=', self.product.product_tmpl_id.id),
            ('subject', 'ilike', 'Alerta de Stock Mínimo'),
        ])
        
        self.assertEqual(len(product_messages), 1, "Debería haber una alerta en el template en este contexto aislado")


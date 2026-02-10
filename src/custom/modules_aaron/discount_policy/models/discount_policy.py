from odoo import models, fields, api

class DiscountPolicy(models.Model):
    _name = 'discount.policy'
    _description = 'Discount Policy'

    name = fields.Char(string="Descripción", required=True)
    active = fields.Boolean(string="Activo", default=True)
    
    rule_ids = fields.One2many('discount.policy.rule', 'policy_id', string="Reglas de Descuento")

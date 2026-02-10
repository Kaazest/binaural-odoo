from odoo import fields, models, api

class ClientType(models.Model):
    _name = "res.client.type"
    _description = "Tipo de Clientes"

    name = fields.Char(string="Tipo de Cliente", required=True)
    description = fields.Char(string="Descripción del tipo")

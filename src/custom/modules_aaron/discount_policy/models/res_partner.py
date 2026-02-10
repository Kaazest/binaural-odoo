from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_type_id = fields.Many2one('res.client.type', string="Tipo de Cliente")
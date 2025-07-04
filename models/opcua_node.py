from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class OpcuaNode(models.Model):
    _name = 'opcua.node'
    _description = 'OPC UA Node'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    node_id = fields.Char(string='Node ID', required=True,
                         help='OPC UA node identifier (e.g., ns=1;s=Temperature)')
    description = fields.Text(string='Description')
    device_id = fields.Many2one('opcua.device', string='Device', required=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    value = fields.Float(string='Current Value', digits=(16, 4))
    last_update = fields.Datetime(string='Last Update')
    error_message = fields.Text(string='Error Message')
    connection_status = fields.Selection([
        ('disconnected', 'Disconnected'),
        ('connected', 'Connected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected', related='device_id.connection_status', store=True)
    data_type = fields.Selection([
        ('float', 'Float'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('string', 'String')
    ], string='Data Type', required=True, default='float')
    unit = fields.Char(string='Unit')
    min_value = fields.Float(string='Minimum Value')
    max_value = fields.Float(string='Maximum Value')
    warning_threshold = fields.Float(string='Warning Threshold')
    critical_threshold = fields.Float(string='Critical Threshold')
    state = fields.Selection([
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('critical', 'Critical')
    ], string='State', default='normal', compute='_compute_state', store=True)

    _sql_constraints = [
        ('node_id_device_uniq', 'unique(node_id, device_id)',
         'Node ID must be unique per device!')
    ] 

    @api.depends('value', 'warning_threshold', 'critical_threshold')
    def _compute_state(self):
        for node in self:
            if node.critical_threshold and node.value >= node.critical_threshold:
                node.state = 'critical'
            elif node.warning_threshold and node.value >= node.warning_threshold:
                node.state = 'warning'
            else:
                node.state = 'normal'

    @api.constrains('node_id', 'device_id')
    def _check_unique_node_id(self):
        for record in self:
            if self.search_count([
                ('node_id', '=', record.node_id),
                ('device_id', '=', record.device_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError('Node ID must be unique per device')

    @api.constrains('min_value', 'max_value')
    def _check_value_range(self):
        for record in self:
            if record.min_value and record.max_value and record.min_value >= record.max_value:
                raise ValidationError('Minimum value must be less than maximum value')

    @api.constrains('warning_threshold', 'critical_threshold')
    def _check_thresholds(self):
        for record in self:
            if record.warning_threshold and record.critical_threshold and record.warning_threshold >= record.critical_threshold:
                raise ValidationError('Warning threshold must be less than critical threshold') 
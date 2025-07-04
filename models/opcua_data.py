from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)

class OpcuaData(models.Model):
    _name = 'opcua.data'
    _description = 'OPC UA Historical Data'
    _order = 'timestamp desc'

    device_id = fields.Many2one('opcua.device', string='Device', required=True, ondelete='cascade')
    node_id = fields.Char('Node ID', required=True)
    node_name = fields.Char('Node Name', related='device_id.node_ids.name', store=True)
    timestamp = fields.Datetime('Timestamp', required=True, default=fields.Datetime.now)
    value = fields.Float('Value', digits=(10, 2))
    error = fields.Text('Error Message')

    _sql_constraints = [
        ('timestamp_node_uniq', 'unique(timestamp, node_id, device_id)',
         'Only one value can be recorded per node at a given timestamp!')
    ]

    @api.model
    def fetch_opcua_data(self):
        """Fetch data from OPC UA server for all active records"""
        records = self.search([('active', '=', True)])
        api_url = 'http://localhost:4001/data'

        for record in records:
            try:
                params = {
                    'endpoint': record.endpoint,
                    'node_ids': record.node_ids
                }
                response = requests.get(api_url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('error'):
                        record.write({
                            'error_message': data['error'],
                            'connection_status': 'error'
                        })
                    else:
                        # Get the first value from the response
                        first_node = record.node_ids.split('\n')[0].strip()
                        value = data['values'].get(first_node)
                        record.write({
                            'value': value,
                            'last_update': fields.Datetime.now(),
                            'error_message': False,
                            'connection_status': data.get('connectionStatus', 'disconnected')
                        })
                else:
                    record.write({
                        'error_message': f'HTTP Error: {response.status_code}',
                        'connection_status': 'error'
                    })
            except Exception as e:
                _logger.error(f"Error fetching OPC UA data for {record.name}: {str(e)}")
                record.write({
                    'error_message': str(e),
                    'connection_status': 'error'
                })

    @api.model
    def test_connection(self):
        """Test connection to OPC UA server"""
        api_url = 'http://localhost:4001/test'
        try:
            response = requests.get(api_url, params={'endpoint': self.endpoint}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'connection_status': data.get('connectionStatus', 'disconnected'),
                    'error_message': data.get('error')
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test',
                        'message': 'Connection successful!' if data.get('connectionStatus') == 'connected' else 'Connection failed',
                        'type': 'success' if data.get('connectionStatus') == 'connected' else 'danger',
                        'sticky': False,
                    }
                }
        except Exception as e:
            self.write({
                'connection_status': 'error',
                'error_message': str(e)
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                    'sticky': False,
                }
            }
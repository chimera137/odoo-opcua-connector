from odoo import models, fields, api
import requests
from datetime import datetime
import logging
import threading
import time
import odoo
from odoo.api import Environment

_logger = logging.getLogger(__name__)

class OpcuaDevice(models.Model):
    _name = 'opcua.device'
    _description = 'OPC UA Device'
    _order = 'name'

    name = fields.Char('Name', required=True)
    endpoint = fields.Char('OPC UA Endpoint', required=True, 
                          help='OPC UA server endpoint (e.g., opc.tcp://server:4840)')
    active = fields.Boolean('Active', default=True)
    error_message = fields.Text('Last Error')
    connection_status = fields.Selection([
        ('disconnected', 'Disconnected'),
        ('connected', 'Connected'),
        ('error', 'Error'),
        ('polling', 'Polling')
    ], string='Connection Status', default='disconnected')
    
    node_ids = fields.One2many('opcua.node', 'device_id', string='Nodes')
    data_count = fields.Integer('Data Points', compute='_compute_data_count')
    is_polling = fields.Boolean('Is Polling', default=False, help='Indicates if the device is currently being polled')
    polling_interval = fields.Integer('Polling Interval (ms)', default=1000, help='Interval between data fetches in milliseconds')
    api_port = fields.Integer(string='API Port', required=True, default=4001)
    api_url = fields.Char(string='API URL', compute='_compute_api_url', store=True)

    @api.depends('node_ids')
    def _compute_data_count(self):
        for device in self:
            device.data_count = len(device.node_ids)

    @api.depends('api_port')
    def _compute_api_url(self):
        for record in self:
            record.api_url = f'http://host.docker.internal:{record.api_port}'

    def test_connection(self):
        self.ensure_one()
        try:
            _logger.info(f"Testing connection for device {self.name} at {self.endpoint}")
            api_url = self.api_url + '/test'
            
            # Use the /test endpoint with GET method
            response = requests.get(api_url, params={'endpoint': self.endpoint}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Update device status based on the response from the API
            self.connection_status = data.get('connectionStatus', 'error')
            
            if data.get('error'):
                error_msg = f"Connection test failed: {data.get('error')}"
                self.error_message = error_msg
                _logger.error(error_msg)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test Failed',
                        'message': error_msg,
                        'type': 'danger',
                        'sticky': True,
                    }
                }
            else:
                success_msg = f"Successfully connected to OPC UA device {self.name} at {self.endpoint}"
                self.error_message = False
                # If polling, keep status as 'polling', else set to 'connected'
                if self.is_polling:
                    self.connection_status = 'polling'
                else:
                    self.connection_status = 'connected'
                _logger.info(success_msg)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test Successful',
                        'message': success_msg,
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Could not connect to OPC UA API at {api_url}. Please ensure the API server is running and accessible."
            self.connection_status = 'error'
            self.error_message = error_msg
            _logger.error(error_msg)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Error',
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            error_msg = f"Error testing connection for device {self.name}: {str(e)}"
            self.connection_status = 'error'
            self.error_message = error_msg
            _logger.error(error_msg)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test Error',
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def fetch_data(self):

        start_time = time.time()
        
        self.ensure_one()
        try:
            api_url = self.api_url + '/data'
            node_ids = [node.node_id for node in self.node_ids]
            # Prepare data to send in the request body
            payload = {
                'endpoint': self.endpoint,
                'node_ids': node_ids
            }
            
            # Use POST method and send data in the body
            response = requests.post(api_url, json=payload, timeout=10) # Increased timeout slightly for POST
            response.raise_for_status()
            data = response.json()
            _logger.info(f"Received data from API: {data}")
            self.connection_status = data.get('connectionStatus', 'error')
            values = data.get('values', {})
            if not isinstance(values, dict):
                values = {}
            _logger.info(f"Extracted values: {values}")
            formatted_values = []
            
            # Find the linked monitor and process data for business logic
            monitor = self.env['device.monitor'].search([('device_id', '=', f'{self._name},{self.id}')], limit=1)
            
            # Update node values and create historical data
            for node_id, value in values.items():
                # Process through device monitor if linked
                if monitor:
                    try:
                        _logger.info(f"Processing via monitor {monitor.name}: Node {node_id} = {value}")
                        monitor._process_plc_data(node_id, value)
                    except Exception as e:
                        _logger.error(f"Error processing data through monitor {monitor.name}: {e}")

                # Find the corresponding node
                node = self.node_ids.filtered(lambda n: n.node_id == node_id)
                if node:
                    # Update node's current value
                    node.write({
                        'value': value,
                        'last_update': fields.Datetime.now(),
                        'error_message': False
                    })
                    # Create historical data point
                    self.env['opcua.data'].create({
                        'device_id': self.id,
                        'node_id': node_id,
                        'timestamp': fields.Datetime.now(),
                        'value': value,
                        'error': data.get('error')
                    })
                    formatted_values.append(f'{node.name}: {value}')

            end_time = time.time()
            duration = end_time - start_time
            latency = duration * 1000
            _logger.info(f"Time taken to fetch data: {latency} ms")
            
            _logger.info(f"Formatted values: {formatted_values}")
            self.error_message = data.get('error')
            if data.get('error'):
                self.connection_status = 'error'
                message = f'Error: {data.get("error")}'
                message_type = 'danger'
            else:
                if not values:
                    message = 'No data received from device'
                    message_type = 'warning'
                else:
                    message = 'Data fetched successfully:\n' + '\n'.join(formatted_values)
                    message_type = 'success'
            _logger.info(f"Final message: {message}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'OPC UA Data',
                    'message': message,
                    'type': message_type,
                    'sticky': bool(data.get('error')),
                }
            }
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Could not connect to OPC UA API at {api_url}. Please ensure the API server is running."
            self.connection_status = 'error'
            self.error_message = error_msg
            _logger.error(error_msg)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Error',
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            error_msg = f"Error fetching data: {str(e)}"
            self.connection_status = 'error'
            self.error_message = error_msg
            _logger.error(f"Error fetching data from {self.endpoint}: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_view_data(self):
        self.ensure_one()
        return {
            'name': 'Historical Data',
            'type': 'ir.actions.act_window',
            'res_model': 'opcua.data',
            'view_mode': 'list,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id}
        }

    def action_clear_historical_data(self):
        self.ensure_one()
        self.env['opcua.data'].search([('device_id', '=', self.id)]).unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Historical Data',
                'message': 'All historical data has been cleared',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_start_polling(self):
        self.ensure_one()
        if self.is_polling:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Polling Already Running',
                    'message': 'Auto fetch is already running for this device.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Create a new cursor for the thread setup
        with self.env.registry.cursor() as cr:
            env = api.Environment(cr, self.env.uid, self.env.context)
            device = env['opcua.device'].browse(self.id)
            
            # Ensure we're not polling and commit this change
            device.write({'is_polling': False})
            cr.commit()
            
            # Start new polling with fresh state
            interval = max(1, int(self.polling_interval / 1000))
            device.write({'is_polling': True, 'connection_status': 'polling'})
            cr.commit()

        def poller(device_id, interval):
            db_name = self.env.cr.dbname
            uid = self.env.uid
            context = self.env.context
            
            while True:
                try:
                    with odoo.registry(db_name).cursor() as cr:
                        env = api.Environment(cr, uid, context)
                        device = env['opcua.device'].browse(device_id)
                        
                        # Check if polling should continue
                        if not device.is_polling:
                            _logger.info(f"Polling stopped for device {device_id}")
                            break
                            
                        _logger.info(f"Polling device {device_id} at interval {interval}s")
                        device.fetch_data()
                        cr.commit()
                        
                        # Sleep outside the cursor context
                        time.sleep(interval)
                except Exception as e:
                    _logger.error(f"Polling thread for device {device_id} crashed: {e}")
                    # Ensure we clean up if there's an error
                    with odoo.registry(db_name).cursor() as cr:
                        env = api.Environment(cr, uid, context)
                        device = env['opcua.device'].browse(device_id)
                        device.write({'is_polling': False, 'connection_status': 'error'})
                        cr.commit()
                    break

        thread = threading.Thread(target=poller, args=(self.id, interval), daemon=True)
        thread.start()
        
        _logger.info(f"Started polling thread for device {self.id}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Polling Started',
                'message': f'Auto fetch started every {self.polling_interval} ms.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_stop_polling(self):
        self.ensure_one()
        if self.is_polling:
            # Use a new cursor to ensure the change is committed
            with self.env.registry.cursor() as cr:
                env = api.Environment(cr, self.env.uid, self.env.context)
                device = env['opcua.device'].browse(self.id)
                device.write({'is_polling': False, 'connection_status': 'connected'})
                cr.commit()
            
            _logger.info(f"Stopped polling for device {self.id}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Polling Stopped',
                    'message': 'Auto fetch stopped.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Polling Not Running',
                    'message': 'No polling thread was running for this device.',
                    'type': 'info',
                    'sticky': False,
                }
            }
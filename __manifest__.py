{
    'name': 'OPC UA Connector',
    'version': '1.0',
    'summary': 'Connect OPC UA devices to Odoo using a REST API',
    'description': """
        This module provides integration with OPC UA devices through a REST API.
        Features:
        - Connect to OPC UA devices
        - Fetch real-time data
        - Monitor device status
        - Automatic data polling
        - Historical data tracking
    """,
    'author': 'Chimera',
    'website': 'https://petra.ac.id/',
    'category': 'Industrial Automation',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/opcua_device_views.xml',
        'views/opcua_data_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
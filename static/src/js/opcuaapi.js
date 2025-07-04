odoo.define('opcua_connector.opcuaapi', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;

    function OpcuaAPI() {
        this.logger = console;
    }

    OpcuaAPI.prototype = {
        _log: function(message, type) {
            const timestamp = new Date().toISOString();
            const logMessage = `[${timestamp}] ${message}`;
            
            switch(type) {
                case 'error':
                    this.logger.error(logMessage);
                    break;
                case 'warn':
                    this.logger.warn(logMessage);
                    break;
                case 'info':
                    this.logger.info(logMessage);
                    break;
                default:
                    this.logger.log(logMessage);
            }
        },

        fetchData: function(params) {
            this._log(`Fetching data from endpoint: ${params.endpoint}`, 'info');
            this._log(`Node IDs to read: ${params.node_ids.join(', ')}`, 'info');
            
            return this._rpc({
                route: '/opcua/fetch_data',
                params: params,
            }).then(function(result) {
                this._log(`Received data: ${JSON.stringify(result)}`, 'info');
                return result;
            }.bind(this)).catch(function(error) {
                this._log(`Error fetching data: ${error.message}`, 'error');
                throw error;
            }.bind(this));
        },

        testConnection: function(params) {
            this._log(`Testing connection to endpoint: ${params.endpoint}`, 'info');
            this._log(`Testing node IDs: ${params.node_ids.join(', ')}`, 'info');
            
            return this._rpc({
                route: '/opcua/test_connection',
                params: params,
            }).then(function(result) {
                this._log(`Connection test result: ${JSON.stringify(result)}`, 'info');
                return result;
            }.bind(this)).catch(function(error) {
                this._log(`Connection test failed: ${error.message}`, 'error');
                throw error;
            }.bind(this));
        }
    };

    return OpcuaAPI;
}); 
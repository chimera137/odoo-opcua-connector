# odoo-opcua-connector
Odoo Module for Connecting OPC UA Devices

## Overview
This repository contains the `odoo-opcua-connector` module, a custom Odoo ERP add-on designed to facilitate direct and configurable communication with OPC UA servers and devices. It is a key component for integrating shop-floor OPC UA-enabled hardware with Odoo's business applications, enabling real-time data acquisition from industrial machinery.

This is a Third Party Module for Odoo ERP.

## Features
- **OPC UA Device Configuration**: Easily add and configure OPC UA servers and nodes directly within Odoo.
- **Node Data Fetching**: Supports configurable fetching of data from specified OPC UA nodes.
- **Automated Polling**: Implements automatic data polling with a configurable interval for near real-time data synchronization.
- **Connection Pooling & Error Handling**: Robust connection management and error reporting for industrial environments.

## System Architecture Context
The `odoo-opcua-connector` module is part of a larger multi-vendor PLC integration system for Odoo ERP. It works alongside:
- [Modbus Connector](https://github.com/chimera137/odoo-modbus-connector)
- [Device Monitor](https://github.com/chimera137/odoo-device-monitor)

This connector handles direct OPC UA communication via a Node.js-based REST API server, exposing device data to Odoo for further business logic integration.

## Getting Started

### Prerequisites
- Odoo ERP (v16.0 or higher recommended) instance.
- Node.js (LTS version recommended) installed on your server.
- An OPC UA server/device for testing (or OPC UA Simulator).

### Installation
1. **Clone this repository:**
   `git clone https://github.com/chimera137/odoo-opcua-connector.git`

2. **Place the module:** Copy the `odoo-opcua-connector` folder into your Odoo custom add-ons path (e.g., /path/to/odoo/addons/)

3. **Update and Install in Odoo:**
    - Restart your Odoo service.
    - Navigate to the Apps menu in your Odoo instance.
    - Click "Update Apps List" (if you don't see the module immediately).
    - Search for "OPC UA Connector" and install the module.

### Running the OPC UA API Server
This Odoo module relies on a companion Node.js server to handle the direct OPC UA communication and expose data via a REST API.

1. **Navigate to the server directory:**
   `cd /path/to/opcua_connector/server/`

2. **Install dependencies:**
   `npm install`

3. **Run the server:**
   `node opcuaapi.js`
   For production, use a process manager like PM2:
   ```
   npm install -g pm2
   pm2 start opcuaapi.js --name opcua_api_server
   ```

## Usage
Once the opcua_connector module is installed in Odoo and the OPC UA API server is running:
1. **Access OPC UA Device Configuration:**
   Navigate to Manufacturing (or a custom menu if defined) -> Configuration -> OPC UA Devices.

2. **Create a New Device:**
   Click the "Create" button to add a new OPC UA device entry.

3. **Enter Device Details:**
   Provide the OPC UA server endpoint and node IDs you wish to monitor.

4. **Data Acquisition:**
   The Node.js server will automatically poll data from the configured OPC UA devices and push it to Odoo according to the defined polling intervals.

### Integrating with Business Logic
This module focuses on establishing connectivity with OPC UA devices and fetching raw industrial data. To integrate this data into Odoo's core Manufacturing applications (e.g., updating production orders, real-time machine status, quality control, inventory deductions), please refer to our complementary module:
[Device Monitor Module Repository](https://github.com/chimera137/odoo-device-monitor)

### Other Connector Modules
For connecting to Modbus TCP/IP devices as part of the multi-vendor integration framework, please explore our dedicated module:
[Modbus Connector Module Repository](https://github.com/chimera137/odoo-modbus-connector)

## Acknowledgement
This project was developed as part of an undergraduate thesis for the Department of Electrical Engineering / Teknik Elektro at Petra Christian University Surabaya, Indonesia. The insights and methodologies explored herein contribute to the academic research in the field of industrial automation (IIoT) and ERP integration. 
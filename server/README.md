# OPC UA Connector Server

This is a standalone OPC UA connector that provides a REST API for reading OPC UA data.

## Features
- OPC UA communication
- Configurable through environment variables
- Automatic reconnection with retry logic
- REST API endpoints for data and configuration
- Real-time data polling

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the server:
```bash
npm start
```

3. Run the OPC UA API:
```bash
node opcuaapi.js
```

## API Endpoints

### POST /data
Read OPC UA node values from a device.

**Request body:**
```json
{
  "endpoint": "opc.tcp://localhost:4840",
  "nodeIds": ["ns=2;s=MyObject.CAM_VALUE", "ns=2;s=MyObject.Temperature"]
}
```

**Response:**
```json
{
  "values": {
    "ns=2;s=MyObject.CAM_VALUE": 55.28,
    "ns=2;s=MyObject.Temperature": 23.66
  },
  "timestamp": "2024-03-14T12:00:00.000Z",
  "error": null,
  "connectionStatus": "connected"
}

```
- All configuration is provided per-request in the body.
- The server manages connections and will reconnect as needed.

## Error Handling
- Automatic reconnection on connection loss
- Detailed error reporting in API responses

## Future Improvements
- Add write operations
- Add support for more OPC UA features
- Add authentication
- Add data validation
- Add more API endpoints for flexibility 
const express = require('express');
const { OPCUAClient, AttributeIds, DataType } = require('node-opcua');
require('dotenv').config();

const app = express();
app.use(express.json()); // For parsing application/json
const port = process.env.API_PORT || 4001;

// Simple connection pool
const connectionPool = new Map();

// Function to get a unique key for each OPC UA server
const getServerKey = (endpoint) => endpoint;

// Function to safely disconnect a client
const safeDisconnect = async (client) => {
    if (client) {
        try {
            await client.disconnect();
        } catch (e) {
            console.error(`Error during disconnect: ${e.message}`);
        }
    }
};

// Simple function to get or create an OPC UA client and session
const getOpcuaClient = async (endpoint) => {
    const key = getServerKey(endpoint);

    // Clean up existing connection if it exists
    if (connectionPool.has(key)) {
        const existingEntry = connectionPool.get(key);
        if (existingEntry.client) {
            await safeDisconnect(existingEntry.client);
        }
        connectionPool.delete(key);
    }

    console.log(`[${new Date().toISOString()}] Creating new client instance for ${endpoint}`);
    const client = OPCUAClient.create({
        endpointMustExist: false
    });

    try {
        // Connect to the server
        console.log(`[${new Date().toISOString()}] Attempting to connect to ${endpoint}...`);
        await client.connect(endpoint);
        console.log(`✅ Client connected to ${endpoint}.`);

        // Create session
        console.log(`[${new Date().toISOString()}] Creating session for ${endpoint}...`);
        const session = await client.createSession();
        console.log(`✅ Session created for ${endpoint}.`);

        // Store in connection pool
        connectionPool.set(key, { client, session });
        return { client, session };
    } catch (error) {
        console.error(`❌ Connection error for ${endpoint}: ${error.message}`);
        await safeDisconnect(client);
        throw error;
    }
};

// Enhanced data endpoint with better error handling and batch operations
app.post('/data', async (req, res) => {

    const start_time = Date.now();

    let nodeIds = req.body.node_ids;
    // Allow single node_id or list of node_ids
    if (typeof nodeIds === 'string') {
        nodeIds = [nodeIds];
    } else if (!Array.isArray(nodeIds)) {
        nodeIds = [];
    }
    const endpoint = req.body.endpoint;

    if (!endpoint || !nodeIds || nodeIds.length === 0) {
        return res.status(400).json({
            error: "Invalid request",
            message: "Missing required parameters (endpoint and node_ids in body)",
            connectionStatus: 'error'
        });
    }

    let result = {
        values: {},
        errors: {},
        connectionStatus: 'disconnected',
        timestamp: new Date().toISOString()
    };

    let clientEntry = null;
    try {
        clientEntry = await getOpcuaClient(endpoint);
        const { client, session } = clientEntry;

        result.connectionStatus = 'connected';
        console.log(`[${new Date().toISOString()}] Attempting to read nodes from ${endpoint}.`);

        // Batch read nodes for better performance
        const nodesToRead = nodeIds.map(nodeId => ({
            nodeId: nodeId,
            attributeId: AttributeIds.Value
        }));

        try {
            const dataValues = await session.read(nodesToRead);
            
            dataValues.forEach((dataValue, index) => {
                const nodeId = nodeIds[index];
                if (dataValue && dataValue.statusCode && dataValue.statusCode.isGood()) {
                    result.values[nodeId] = dataValue.value.value;
                    console.log(`[${new Date().toISOString()}] Read node ${nodeId}:`, dataValue.value.value);
                } else {
                    const status = dataValue && dataValue.statusCode ? dataValue.statusCode.toString() : 'Bad StatusCode';
                    console.warn(`[${new Date().toISOString()}] Failed to read node ${nodeId}: Bad StatusCode - ${status}`);
                    result.values[nodeId] = null;
                    result.errors[nodeId] = `Bad StatusCode: ${status}`;
                }
            });
        } catch (readError) {
            console.error(`[${new Date().toISOString()}] Batch read error: ${readError.message}`);
            result.error = `Batch read error: ${readError.message}`;
        }
    } catch (error) {
        result.error = error.message;
        result.connectionStatus = 'error';
        console.error(`[${new Date().toISOString()}] OPC UA data fetch error:`, error.message);
    }

    res.json(result);
    const end_time = Date.now();
    const duration = end_time - start_time;
    const latency = duration;
    console.log(`[${new Date().toISOString()}] Time taken to fetch data: ${latency} ms`);
});

// Test endpoint: Test connection to OPC UA server
app.get('/test', async (req, res) => {
    const endpoint = req.query.endpoint;

    if (!endpoint) {
        return res.status(400).json({
            error: "Invalid request",
            message: "Missing endpoint parameter",
            connectionStatus: 'error'
        });
    }

    let result = {
        error: null,
        connectionStatus: 'disconnected'
    };
    
    try {
        await getOpcuaClient(endpoint);
        result.connectionStatus = 'connected';
        console.log(`[${new Date().toISOString()}] Connection test successful for ${endpoint}.`);
    } catch (error) {
        result.error = error.message;
        result.connectionStatus = 'error';
        console.error(`[${new Date().toISOString()}] OPC UA test connection error:`, error.message);
    }

    res.json(result);
});

// Start the server
app.listen(port, () => {
    console.log(`🌐 OPC UA REST API running at http://host.docker.internal:${port}`);
    console.log(`📝 Data endpoint: POST http://host.docker.internal:${port}/data (requires endpoint and node_ids in body)`);
    console.log("API server is ready to receive data requests with device configurations.");
});
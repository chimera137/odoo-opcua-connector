import asyncio
from asyncua import Server
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Create server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("OPC UA Simulation Server")

    # Set up our own namespace
    uri = "http://example.org"
    idx = await server.register_namespace(uri)

    # Get the Objects node
    objects = server.get_objects_node()

    # Create a device object
    device = await objects.add_object(idx, "Device1")
    
    # Create multiple tags with different data types
    tags = {
        "Tag1": {"type": "Float", "value": 0.0, "min": 0.0, "max": 100.0},
        "Tag2": {"type": "Int", "value": 0, "min": 0, "max": 1000},
        "Tag3": {"type": "Bool", "value": False},
        "Tag4": {"type": "String", "value": "Initial Value"},
        "Tag5": {"type": "Float", "value": 0.0, "min": -50.0, "max": 50.0}
    }

    # Create variables for each tag
    variables = {}
    for tag_name, tag_info in tags.items():
        if tag_info["type"] == "Float":
            variables[tag_name] = await device.add_variable(idx, tag_name, tag_info["value"])
        elif tag_info["type"] == "Int":
            variables[tag_name] = await device.add_variable(idx, tag_name, tag_info["value"])
        elif tag_info["type"] == "Bool":
            variables[tag_name] = await device.add_variable(idx, tag_name, tag_info["value"])
        elif tag_info["type"] == "String":
            variables[tag_name] = await device.add_variable(idx, tag_name, tag_info["value"])
        
        # Set the variable to be writable
        await variables[tag_name].set_writable()
        logger.info(f"Created variable: {tag_name}")

    # Start the server
    async with server:
        logger.info("Server started at {}".format(server.endpoint))
        
        # Update values periodically
        while True:
            for tag_name, tag_info in tags.items():
                if tag_info["type"] == "Float":
                    new_value = random.uniform(tag_info["min"], tag_info["max"])
                elif tag_info["type"] == "Int":
                    new_value = random.randint(tag_info["min"], tag_info["max"])
                elif tag_info["type"] == "Bool":
                    new_value = random.choice([True, False])
                elif tag_info["type"] == "String":
                    new_value = f"Value_{random.randint(1, 100)}"
                
                await variables[tag_name].write_value(new_value)
                logger.info(f"Updated {tag_name}: {new_value}")
            
            await asyncio.sleep(1)  # Update every second

if __name__ == "__main__":
    asyncio.run(main()) 
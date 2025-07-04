from opcua import Server, ua
import time
import random

# Setup server
server = Server()
server.set_endpoint("opc.tcp://0.0.0.0:4841")
server.set_server_name("FreeOpcUa Simulation Server")

# Setup a namespace
uri = "http://examples.freeopcua.github.io"
idx = server.register_namespace(uri)

# Make and Configure Objects
objects = server.get_objects_node()
myobj = objects.add_object(idx, "MyObject")
temperature = myobj.add_variable(ua.NodeId("MyObject.Temperature", idx), "Temperature", 20.0)
pressure = myobj.add_variable(ua.NodeId("MyObject.Pressure", idx), "Pressure", 1.0)
humidity = myobj.add_variable(ua.NodeId("MyObject.Humidity", idx), "Humidity", 50.0)
temperature.set_writable()
pressure.set_writable()
humidity.set_writable()
CAM_VALUE = myobj.add_variable(ua.NodeId("MyObject.CAM_VALUE", idx), "CAM_VALUE", 0.0)
CAM_VALUE.set_writable()

# Start server
server.start()
print("OPC UA Simulation Server started at opc.tcp://localhost:4841")
try:
    while True:
        temperature.set_value(20.0 + random.random() * 10)
        pressure.set_value(1.0 + random.random() * 0.5)
        humidity.set_value(40.0 + random.random() * 20)
        CAM_VALUE.set_value(random.random() * 100)
        time.sleep(5)
except KeyboardInterrupt:
    print("Shutting down server...")
finally:
    server.stop()
import time

from zeroconf import ServiceBrowser, ServiceStateChange
from zeroconf import Zeroconf


IDENTIFIER = "restsysmon"


class ZeroScanner:
    def __init__(self, identifier=IDENTIFIER):
        self.zero = None
        self.browser = None
        self.nodes = {}
        self.running = False
        self.identifier = identifier.encode("utf-8")

    def get_nodes(self):
        return self.nodes

    def on_new_node(self, node):
        print(node)
        node["last_seen"] = time.time()
        self.nodes[f'{node["name"]}:{node["host"]}'] = node

    def on_node_update(self, node):
        node["last_seen"] = time.time()
        self.nodes[f'{node["name"]}:{node["host"]}'] = node

    def on_service_state_change(self, zeroconf, service_type, name,
                                state_change):

        if state_change is ServiceStateChange.Added or state_change is \
                ServiceStateChange.Updated:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.properties:
                for key, value in info.properties.items():
                    if key == b"type" and value == self.identifier:
                        host = info._properties[b"host"].decode("utf-8")
                        port = info._properties[b"port"].decode("utf-8")
                        name = info._properties[b"name"].decode("utf-8")
                        node = {"host": host, "port": port, "name": name}
                        if state_change is ServiceStateChange.Added:
                            self.on_new_node(node)
                        else:
                            self.on_node_update(node)

    def start(self):
        self.zero = Zeroconf()
        self.browser = ServiceBrowser(self.zero, "_http._tcp.local.",
                                      handlers=[self.on_service_state_change])
        self.running = True

    def stop(self):
        if self.zero:
            self.zero.close()
        self.zero = None
        self.browser = None
        self.running = False

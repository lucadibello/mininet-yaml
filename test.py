from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo

from modules.models.topology import NetworkTopology
from modules.yaml.decoder import decodeTopology

class CustomTopology(Topo):
    class LinuxRouter(Node):
        def config(self, **params):
            super().config(**params)
            self.cmd('sysctl net.ipv4.ip_forward=1')

        def terminate(self):
            self.cmd('sysctl net.ipv4.ip_forward=0')
            super().terminate()
    
    def build(self, topology: NetworkTopology):
        for router in topology.get_routers():
            self.addHost(router.get_name(), cls=self.LinuxRouter)
        for host in topology.get_hosts():
            self.addHost(host.get_name())

        self.addLink("r1", "h1")

def main():
    topology = decodeTopology("topology.example.yaml")

    net = Mininet(topo=CustomTopology(topology))
    net.start()
    net.stop()

if __name__ == "__main__":
    main()
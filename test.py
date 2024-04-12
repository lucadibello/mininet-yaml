from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate( self ):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


def run():
    "Basic example"
    net = Mininet(topo=None, cleanup=True, autoSetMacs=True)
    net.addController('c0', protocols='OpenFlow13')

    switch = net.addSwitch('s1')
    host1 = net.addHost('h1')
    host2 = net.addHost('h2')

    net.addLink(host1, switch)
    net.addLink(host2, switch)

    net.start()

    host1.setIP('10.0.1.1', 24, intf='h1-eth0')
    host2.setIP('10.0.1.2', 24, intf='h2-eth0')

    # host1.setDefaultRoute('dev H1-eth0 via 10.0.1.254')
    # host2.setDefaultRoute('dev H2-eth0 via 10.0.2.254')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
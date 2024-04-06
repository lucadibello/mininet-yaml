from typing import Sequence
from modules.models.network_elements import NetworkElement
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI

from modules.util.logger import Logger


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class VirtualNetworkTopology(Topo):

    def _create_nodes(self, elements: Sequence[NetworkElement], **additional_host_arguments):
        """
        Creates the nodes in the virtual network.

        Args:
                elements (list[NetworkElement]): The network elements to create.
        """
        for element in elements:
            virt_element = self.addHost(
                element.get_name(), ip=None, **additional_host_arguments)

            yield element, virt_element

    def build(self, network: NetworkTopology):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
                network (NetworkTopology): The network topology to virtualize.
        """

        Logger().debug("Building the virtual network topology...")

        # Hashmap to link network elements to Mininet nodes
        network_elements = {}

        # Create all routers in the network
        for element, virt_element in self._create_nodes(network.get_routers(), cls=LinuxRouter):
            # Add link to Mininet node
            Logger().debug(
                f"Created virtual node: {element.get_name()} (element: {type(element).__name__})")
            network_elements[element] = virt_element
        for element, virt_element in self._create_nodes(network.get_hosts()):
            # Add link to Mininet node
            Logger().debug(
                f"Created virtual node: {element.get_name()} (element: {type(element).__name__})")
            network_elements[element] = virt_element

        # Create links between network elements
        for element in network.get_routers() + network.get_hosts():
            # Get links for this element
            links = element.get_links()
            for link in links:
                # Get the virtualized elements
                source = network_elements[element]
                destination = network_elements[link.endpoint.entity]

                # Create the link
                self.addLink(
                    source, destination,
                    intfName1=link.interface.get_name(), params1=f"{link.interface.get_ip()}/{link.interface.get_prefix_length()}",
                    intfName2=link.endpoint.interface.get_name(), params2=f"{link.endpoint.interface.get_ip()}/{link.endpoint.interface.get_prefix_length()}",
                )

                # Print the link
                Logger().debug(
                    f"Created link between {element.get_name()} ({link.interface.get_ip()}/{link.interface.get_prefix_length()}) and {link.endpoint.entity.get_name()} ({link.endpoint.interface.get_ip()}/{link.endpoint.interface.get_prefix_length()}): {link.interface.get_name()} -> {link.endpoint.interface.get_name()}")


def run_virtual_topology(network: NetworkTopology):
    net = Mininet(topo=VirtualNetworkTopology(network), controller=None)
    # net.start()
    # CLI(net)
    # net.stop()

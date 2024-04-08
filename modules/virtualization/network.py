from typing import Sequence
from modules.models.network_elements import NetworkElement, NetworkInterface
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.clean import cleanup

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

        def _get_link_endpoint_name(element: NetworkElement, interface: NetworkInterface):
            return f"{element.get_name()}-{interface.get_name()}"

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
        added_links = set()
        for element in network.get_routers() + network.get_hosts():
            Logger().debug("Creating links for element: " + element.get_name())

            # Add all links connected to the current element
            for link in element.get_links():
                # Format interface names
                source_nic_name = _get_link_endpoint_name(
                    element, link.interface)
                destination_nic_name = _get_link_endpoint_name(
                    link.endpoint.entity, link.endpoint.interface)

                # Format IP addresses
                source_ip = link.interface.get_ip_subnet()
                destination_ip = link.endpoint.interface.get_ip_subnet()

                # Check if the link has already been added
                if (source_nic_name, destination_nic_name) or (destination_nic_name, source_nic_name) in added_links:
                    continue

                # Create the link
                self.addLink(
                    # Virtual source node name
                    network_elements[element],
                    # Virtual destination node name
                    network_elements[link.endpoint.entity],
                    # Source node link info
                    intfName1=source_nic_name, params1={
                        "ip": source_ip
                    },
                    # Destination node link info
                    intfName2=destination_nic_name, params2={
                        "ip": destination_ip
                    }
                )

                # Add link to set
                added_links.add((source_nic_name, destination_nic_name))

                # Print the link
                Logger().debug(
                    f"Created link between {element.get_name()} ({link.interface.get_ip()}/{link.interface.get_prefix_length()}) and {link.endpoint.entity.get_name()} ({link.endpoint.interface.get_ip()}/{link.endpoint.interface.get_prefix_length()}): {link.interface.get_name()} -> {link.endpoint.interface.get_name()}")


def run_virtual_topology(network: NetworkTopology):
    # Before starting the virtual network, clean up any previous Mininet instances
    cleanup()
    # Start the virtual network passing the decoded network topology
    net = Mininet(topo=VirtualNetworkTopology(network), controller=None)
    # Start the virtual network
    net.start()
    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()

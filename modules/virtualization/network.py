from typing import Sequence
from modules.models.network_elements import Host, NetworkElement, NetworkInterface
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class VirtualNetworkTopology(Topo):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _generate_link_endpoint_name(source: NetworkElement, source_interface: NetworkInterface, destination: NetworkElement):
        return f"{source.get_name()}-{source_interface.get_name()}-{destination.get_name()}"

    def _create_nodes(self, elements: Sequence[NetworkElement], virtual_elements_lookup_table: dict[NetworkElement, str], **kwargs):
        for element in elements:
            # Create the node
            virtual_element = self.addHost(element.get_name(), ip=None, **kwargs)
            # Add the node to the lookup table
            virtual_elements_lookup_table[element] = virtual_element

    def _create_links(self, elements: Sequence[NetworkElement], virtual_elements_lookup_table: dict[NetworkElement, str]):

        # Create links between network elements
        added_links = set()
        for element in elements: 
            Logger().debug(f"Creating links for element {element.get_name()}. Found links: {len(element.get_links())}")
             
            # Add all links connected to the current element
            for link in element.get_links():
                
                # Skip links that are connected to simple hosts!
                if isinstance(link.endpoint.entity, Host):
                    print("Skipped link to host")
                    continue

                # Format interface names
                source_nic_name = VirtualNetworkTopology._generate_link_endpoint_name(
                    element, link.interface, link.endpoint.entity)
                destination_nic_name = VirtualNetworkTopology._generate_link_endpoint_name(
                    link.endpoint.entity, link.endpoint.interface, element)

                # Format IP addresses
                source_ip = link.interface.get_ip_with_prefix()
                destination_ip = link.endpoint.interface.get_ip_with_prefix()

                # Check if the link has already been added (links are bidirectional, so one entry is enough for both directions)
                if (source_nic_name, destination_nic_name) in added_links or (destination_nic_name, source_nic_name) in added_links:
                    continue

                # Create the link
                self.addLink(
                    # Virtual source node name
                    virtual_elements_lookup_table[element],
                    # Virtual destination node name
                    virtual_elements_lookup_table[link.endpoint.entity],

                    # Source node link info
                    intfName1=source_nic_name,
                    params1={
                        "ip": source_ip
                    },

                    # Destination node link info
                    intfName2=destination_nic_name,
                    params2={
                        "ip": destination_ip
                    }
                )

                # Add link to set
                added_links.add((source_nic_name, destination_nic_name))

                # Print the link
                Logger().info(f"Created link between {element.get_name()} ({link.interface.get_ip()}/{link.interface.get_prefix_length()}) and {link.endpoint.entity.get_name()} ({link.endpoint.interface.get_ip()}/{link.endpoint.interface.get_prefix_length()}): {link.interface.get_name()} -> {link.endpoint.interface.get_name()}")
        
    def _build_network(self, subnets: Sequence[Ipv4Subnet], virtual_elements_lookup_table: dict[NetworkElement, str]):
        switch_counter=0
        for subnet in subnets:
            # If the subnet has only one host, a switch is not needed!
            if len(subnet.get_hosts()) <= 1: 
                # Connect the host directly to the router
                for host in subnet.get_hosts():
                    host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}-{host.entity.get_name()}"
                    router_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}-{host.entity.get_name()}"
                    virtual_router = virtual_elements_lookup_table[host.entity]
                    self.addLink(
                        virtual_router,
                        virtual_router,
                        # Source interface (Host)
                        intfName1=host_intf_name,
                        params1={
                            "ip": host.interface.get_ip_with_prefix()
                        },
                        # Destination interface (Router)
                        intfName2=router_intf_name,
                        params2={
                            "ip": host.interface.get_ip_with_prefix()
                        },
                    )
            else:
                # Create the switch
                switch = self.addSwitch(f"s{switch_counter}")
                # Increment the switch counter
                switch_counter += 1

                Logger().debug(f"Created switch {switch} for subnet {subnet.network_address()}")

                # Connect switch to all subnet routers
                for router in subnet.get_routers():
                    virtual_router = virtual_elements_lookup_table[router.entity]
                    switch_intf_name = f"{switch}-{router.interface.get_name()}-{router.entity.get_name()}"
                    router_intf_name = f"{router.entity.get_name()}-{router.interface.get_name()}-{switch}"
                    
                    self.addLink(
                        switch,
                        virtual_router,

                        # Source interface (Switch)
                        intfName1=switch_intf_name,
                        # params1={
                        #     "ip": subnet.get_gateway()
                        # },
                        
                        # Destination interface (Router)
                        intfName2=router_intf_name,
                        params2={
                            "ip": router.interface.get_ip_with_prefix()
                        },
                    )

                # Connect the switch to all hosts in the subnet
                for host in subnet.get_hosts():
                    switch_intf_name = f"{switch}-{host.interface.get_name()}-{host.entity.get_name()}"
                    host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}-{switch}"
                    virtual_host = virtual_elements_lookup_table[host.entity] 
                    self.addLink(
                        switch,
                        virtual_host,
                        # Source interface (Switch)
                        intfName1=switch_intf_name,
                        # params1={
                        #     "ip": subnet.get_gateway()
                        # },
                        
                        # Destination interface (Host)
                        intfName2=host_intf_name,
                        params2={
                            "ip": host.interface.get_ip_with_prefix()
                        },
                    )

    def build(self, network: NetworkTopology):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
            network (NetworkTopology): The network topology to virtualize.
        """

        Logger().info("Building the virtual network topology...")

        virtual_elements_lookup_table = dict[NetworkElement, str]()

        # Create empty nodes for each router and host
        self._create_nodes(network.get_routers(), virtual_elements_lookup_table, cls=LinuxRouter)
        self._create_nodes(network.get_hosts(), virtual_elements_lookup_table)

        # Create switches for each subnet and connect them to the routers and hosts
        self._build_network(network.get_subnets(), virtual_elements_lookup_table)
        
        # Create all links between routers
        self._create_links(network.get_routers(), virtual_elements_lookup_table)
            
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

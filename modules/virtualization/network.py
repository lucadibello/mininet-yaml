from typing import Sequence, cast
from modules.models.network_elements import Host, NetworkElement, NetworkInterface, Router
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet
from modules.virtualization.network_elements import VirtualHost, VirtualNetworkElement, VirtualRouter

from itertools import chain


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class VirtualNetwork:
    def __init__(self):
        self._virtual_routers = list[VirtualRouter]()
        self._virtual_hosts = list[VirtualHost]()
        self._net: Mininet | None = None # type: ignore
        
    def set_network(self, net: Mininet):
        self._net = net

    def get_node(self, virtual_element: VirtualNetworkElement) -> Node:
        if not self._net:
            raise ValueError("The virtual network has not been linked to the Mininet instance yet!")
        # Force type cast to Node (Mininet node)
        return cast(Node, self._net.get(virtual_element.get_name()))
    
    def add_virtual_router(self, router: VirtualRouter):
        self._virtual_routers.append(router)
    
    def get_virtual_routers(self) -> list[VirtualRouter]:
        return self._virtual_routers

    def add_virtual_host(self, host: VirtualHost):
        self._virtual_hosts.append(host)
    

class VirtualNetworkTopology(Topo):

    @staticmethod
    def _generate_link_endpoint_name(source: NetworkElement, source_interface: NetworkInterface, destination: NetworkElement):
        return f"{source.get_name()}-{source_interface.get_name()}-{destination.get_name()}"

    def _create_nodes(self, elements: Sequence[NetworkElement], virtual_elements_lookup_table: dict[NetworkElement, str], **kwargs):
        for element in elements:
            # Create the node
            virtual_element = self.addHost(element.get_name(), ip=None, **kwargs)
            # Add the node to the lookup table
            virtual_elements_lookup_table[element] = virtual_element
            # Yield the element and the virtual element
            yield element

    def _create_links(self, elements: Sequence[NetworkElement], virtual_elements_lookup_table: dict[NetworkElement, str]):

        # Create links between network elements
        added_links = set()
        for element in elements: 
            Logger().debug(f"Creating links for element {element.get_name()}. Found links: {len(element.get_links())}")
             
            # Add all links connected to the current element
            for link in element.get_links():
                
                # Skip links that are connected to simple hosts as they have already been handled
                if isinstance(link.endpoint.entity, Host):
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
                # Generate a new management IP for the Switch in this particular subnet
                switch_ip = subnet.get_next_management_ip()
                switch_ip_with_prefix = f"{switch_ip}/{subnet.get_prefix_length()}"
                
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
                        params1={
                             "ip": switch_ip_with_prefix
                        },
                        
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
                        params1={
                            "ip": switch_ip_with_prefix
                        },
                        
                        # Destination interface (Host)
                        intfName2=host_intf_name,
                        params2={
                            "ip": host.interface.get_ip_with_prefix()
                        },
                    )

    def build(self, network: NetworkTopology, virtual_network: VirtualNetwork):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
            network (NetworkTopology): The network topology to virtualize.
        """

        Logger().info("Building the virtual network topology...")

        virtual_elements_lookup_table = dict[NetworkElement, str]()

        # Create empty nodes for each router and host
        for element in chain(
            self._create_nodes(network.get_routers(), virtual_elements_lookup_table, cls=LinuxRouter),
            self._create_nodes(network.get_hosts(), virtual_elements_lookup_table)
        ):
            # Check if the element is a router or a host
            if isinstance(element, Router):
                virtual_router = VirtualRouter(name=element.get_name(), physical_router=element)
                virtual_network.add_virtual_router(virtual_router)
            else: # then it is a host
                virtual_host = VirtualHost(name=element.get_name(), physical_host=element)
                virtual_network.add_virtual_host(virtual_host)

        # Create switches for each subnet and connect them to the routers and hosts
        self._build_network(network.get_subnets(), virtual_elements_lookup_table)
        
        # Create all links between routers
        self._create_links(network.get_routers(), virtual_elements_lookup_table)
            
def run_virtual_topology(network: NetworkTopology):
    # Before starting the virtual network, clean up any previous Mininet instances
    cleanup()
    # Create empty virtual network
    virtual_network = VirtualNetwork()
    # Start the virtual network passing the decoded network topology
    net = Mininet(topo=VirtualNetworkTopology(network=network, virtual_network=virtual_network), controller=None)
    # Link the virtual network to the virtual network object
    virtual_network.set_network(net)
    # Start the virtual network
    net.start()

    Logger().info("Network topology virtualized successfully! Configuring routing tables...")

    # Build routing table for each virtual router in the network
    for virtual_router in virtual_network.get_virtual_routers():
        # Build the routing table for the router
        Logger().debug(f"Configuring routing table for {virtual_router.get_physical_element().get_name()}...")
        for interface in virtual_router.get_physical_element().get_interfaces():
            # Add the route to the routing table
            virtual_network.get_node(virtual_router).cmd(f"ip route add {interface.get_subnet().network_address()} via {interface.get_ip()} dev {interface.get_name()}")
            Logger().debug(f"Added route to {interface.get_subnet().network_address()} via {interface.get_ip()} on {interface.get_name()}")
    
    Logger().info("Routing tables configured successfully! Starting the Mininet CLI...")
    
    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()

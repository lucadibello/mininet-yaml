from typing import Sequence
from modules.models.network_elements import NetworkElement, NetworkInterface, Router
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet
from modules.virtualization.mininet_types import LinuxRouter
from modules.virtualization.network_elements import VirtualHost, VirtualNetwork, VirtualNetworkElement, VirtualNetworkInterface, VirtualRouter
from modules.exploration.explore import compute_routers_shortest_path

from itertools import combinations

class VirtualNetworkTopology(Topo): 

    def _display_links(self):
        print("== NETWORK LINKS ==")
        # Pretty print the created links
        for link in self.links(True, True, True):
            src_node = link[0]
            dst_node = link[1]
            info = link[3] # type: ignore
            print(f"{src_node} ({info['intfName1']}) <--> {dst_node} ({info['intfName2']})")
                
 
    def _does_link_exist(self, src: str, dst: str, link: tuple[str,str]) -> bool:
        """This method checks if a link between two nodes, with the specified interfaces, already exists in the topology.

        Args:
            src (str): Source node name
            dst (str): Destination node name
            link (tuple[str,str]): Tuple containing source and destination interface names

        Returns:
            bool: True if the link exists, False otherwise
        """
        for entry in self.links(True, True, True):
            src_node = entry[0] # type: ignore
            dst_node = entry[1] # type: ignore
            info = entry[3] # type: ignore
            intfname1 = info["intfName1"]
            intfname2 = info["intfName2"]

            if (src_node == src and dst_node == dst and intfname1 == link[0] and intfname2 == link[1]) or (src_node == dst and dst_node == src and intfname1 == link[1] and intfname2 == link[0]):
                return True
        return False

    def _create_nodes(self, elements: Sequence[NetworkElement], **kwargs):
        """This methods creates virtual nodes for each NetworkElement in the list.

        Args:
            elements (Sequence[NetworkElement]): Sequence of NetworkElements
        """
        for element in elements:
            # Create the node with the same name as the NetworkElement
            self.addHost(element.get_name(), ip=None, **kwargs)

    def _link_routers(self, routers: list[Router]):
        # Compute shortest path between routers
        distance, previous = compute_routers_shortest_path(routers)

        # Sort routers by distance
        sorted_routers = sorted(routers, key=lambda router: distance[router])
        
        # Start linking routers
        for router in sorted_routers:
            previous_router = previous[router]
            if previous_router:
                # Get the interfaces to link
                src_interface = router.get_interface_to(previous_router)
                dst_interface = previous_router.get_interface_to(router)
                # Generate interface names
                src_intf_name = f"{router.get_name()}-{src_interface.get_name()}"
                dst_intf_name = f"{previous_router.get_name()}-{dst_interface.get_name()}"
                # Check if link already exists
                if self._does_link_exist(
                    src=router.get_name(),
                    dst=previous_router.get_name(),
                    link=(src_intf_name, dst_intf_name)
                ):
                    Logger().info(f"\t [!] link between {router.get_name()} (vintf: {src_intf_name}) and {previous_router.get_name()} (vintf: {dst_intf_name}) already exists. Skipping...")
                    continue
                # Create the link
                self.addLink(
                    router.get_name(),
                    previous_router.get_name(),
                    # Source interface
                    intfName1=src_intf_name,
                    params1={
                        "ip": src_interface.get_ip_with_prefix()
                    },
                    # Destination interface
                    intfName2=dst_intf_name,
                    params2={
                        "ip": dst_interface.get_ip_with_prefix()
                    },
                )
                self._display_links()


    def _link_hosts_routers(self, subnets: Sequence[Ipv4Subnet], virtual_elements_lookup_table: dict[NetworkElement, VirtualNetworkElement]):
        switch_counter=0
        for subnet in subnets:
            hosts = subnet.get_hosts()
            routers = subnet.get_routers()

            # Skip empty subnets
            if len(hosts) == 0: # subnet has no hosts
                continue

            if len(hosts) == 1: # subnet has only one host, connect directly to router
                host = hosts[0]
                for router in routers:	
                    # Generate interface names
                    host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}"
                    router_intf_name = f"{router.entity.get_name()}-{router.interface.get_name()}"

                    # Check if link already exists
                    if self._does_link_exist(
                        src=host.entity.get_name(),
                        dst=router.entity.get_name(),
                        link=(host_intf_name, router_intf_name)
                    ):
                        Logger().info(f"\t [!] link between {host.entity.get_name()} (vintf: {host_intf_name}) and {router.entity.get_name()} (vintf: {router_intf_name}) already exists. Skipping...")
                        continue
        
                    # Register virtual interface names in both elements
                    virtual_router = virtual_elements_lookup_table[router.entity]
                    virtual_router.add_virtual_interface(VirtualNetworkInterface(
                        router_intf_name,
                        router.interface,
                    ))
                    virtual_host = virtual_elements_lookup_table[host.entity]
                    virtual_host.add_virtual_interface(VirtualNetworkInterface(
                        host_intf_name,
                        host.interface,
                    ))	
 
                    # Create the link
                    self.addLink(
                        host.entity.get_name(),
                        router.entity.get_name(),
                        # Source interface (Host)
                        intfName1=host_intf_name,
                        params1={
                            "ip": host.interface.get_ip_with_prefix()
                        },
                        # Destination interface (Router)
                        intfName2=router_intf_name,
                        params2={
                            "ip": router.interface.get_ip_with_prefix()
                        },
                    )
                    self._display_links()
            else:
                # Generate a new management IP for the Switch in this particular subnet
                switch_ip = subnet.get_next_management_ip()
                switch_ip_with_prefix = f"{switch_ip}/{subnet.get_prefix_length()}"
                
                # Create the switch 
                switch = self.addSwitch(f"s{switch_counter}")

                # Save virtual switch in the lookup table
                virtual_switch = VirtualNetworkElement(switch)

                # Increment the switch counter
                switch_counter += 1

                Logger().debug(f"Created switch {switch} for subnet {subnet.network_address()}")

                # Connect switch to all subnet routers
                for router in subnet.get_routers():
                    # Generate interface names
                    switch_intf_name = f"{switch}-eth0"
                    router_intf_name = f"{router.entity.get_name()}-{router.interface.get_name()}"

                    # Check if the link has already been found by other network elements
                    if self._does_link_exist(
                        src=switch,
                        dst=router.entity.get_name(),
                        link=(switch_intf_name, router_intf_name)
                    ):
                        Logger().info(f"\t [!] link between switch {switch} (vintf: {switch_intf_name}) and router {router.entity.get_name()} (vintf: {router_intf_name}) already exists. Skipping...")
                        continue

                    # Register virtual interface names
                    virtual_router = virtual_elements_lookup_table[router.entity]
                    virtual_router.add_virtual_interface(VirtualNetworkInterface(
                        router_intf_name,
                        router.interface,
                    ))
                    virtual_switch.add_virtual_interface(VirtualNetworkInterface(
                        switch_intf_name,
                        NetworkInterface(
                            name="eth0",
                            ip=switch_ip,
                            mask=subnet.get_mask(),
                        )
                    ))

                    Logger().debug(f"\t * connecting router {router.entity.get_name()} (vintf: {router_intf_name}) to switch {switch} (vintf: {switch_intf_name})")
                    self.addLink(
                        switch,
                        router.entity.get_name(),

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
                    # Generate interface names
                    switch_intf_name = f"{switch}-eth1"
                    host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}"

                    # Check if link already exists
                    if self._does_link_exist(
                        src=switch,
                        dst=host.entity.get_name(),
                        link=(switch_intf_name, host_intf_name)
                    ):
                        Logger().info(f"\t [!] link between {host.entity.get_name()} (vintf: {host_intf_name}) and switch {switch} (vintf: {switch_intf_name}) already exists. Skipping...")
                        continue

                    # Register virtual interface names
                    virtual_host = virtual_elements_lookup_table[host.entity]
                    virtual_host.add_virtual_interface(VirtualNetworkInterface(
                        host_intf_name,
                        host.interface,
                    ))
                    virtual_switch.add_virtual_interface(VirtualNetworkInterface(
                        switch_intf_name,
                        NetworkInterface(
                            name="eth1",
                            ip=switch_ip,
                            mask=subnet.get_mask(),
                        )
                    ))

                    Logger().debug(f"\t * connecting host {host.entity.get_name()} (vintf: {host_intf_name}) to switch {switch} (vintf: {switch_intf_name})")
                    self.addLink(
                        switch,
                        host.entity.get_name(),
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

                    self._display_links()
                # Yield important information about the created switch
                yield virtual_switch

    def build(self, network: NetworkTopology, virtual_network: VirtualNetwork):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
            network (NetworkTopology): The network topology to virtualize.
        """

        Logger().info("Building the virtual network topology...")

        virtual_elements_lookup_table = dict[NetworkElement, VirtualNetworkElement]()

        # Add routers to topology
        self._create_nodes(network.get_routers(), cls=LinuxRouter)
        for router in network.get_routers():
            # Create virtual network element
            virtual_router = VirtualRouter(physical_router=router)
            virtual_network.add_virtual_router(virtual_router)
            # Register element in lookup table
            virtual_elements_lookup_table[router] = virtual_router

        # Add hosts to topology
        self._create_nodes(network.get_hosts())
        for host in network.get_hosts():
            # Create virtual network element
            virtual_host = VirtualHost(physical_host=host)
            virtual_network.add_virtual_host(virtual_host)
            # Register host in lookup table
            virtual_elements_lookup_table[host] = virtual_router

        # Create links between interconnected routers
        # FIXME: Enable link routers
        self._link_routers(network.get_routers())

        # # For each subnet, create a switch (if needed) and connect hosts to routers
        # for virtual_switch in self._link_hosts_routers(network.get_subnets(), virtual_elements_lookup_table):
        # 	# Add the switch to the virtual network
        # 	virtual_network.add_virtual_switch(virtual_switch)
        
        # Notify that the topology has been constructed
        Logger().info("The virtual network topology has been built.")
            
def run_virtual_topology(network: NetworkTopology):
    # Create empty virtual network
    virtual_network = VirtualNetwork()

    # Cleanup any previous Mininet instances
    cleanup()

    # Start the virtual network passing the decoded network topology
    net = Mininet(
        topo=VirtualNetworkTopology(
            network=network, # pass decoded network topology
            virtual_network=virtual_network # pass store for virtual network elements (Mininet nodes + their virtual interfaces)
        ),
        build=True,
        autoSetMacs=True,
        waitConnected=True,
    )
    # Link the virtual network to the virtual network object
    virtual_network.set_network(net)

    # Start Mininet
    Logger().info("Starting the virtual network...")
    net.start()

    Logger().info("Network topology virtualized successfully! Configuring routing tables...")

    # Build routing table for each virtual router in the network
    # for virtual_router in virtual_network.get_virtual_routers():
    #     # Build the routing table for the router
    #     Logger().debug(f"Configuring routing table for {virtual_router.get_physical_element().get_name()}...")
        
    #     # Get mininet node object
    #     node = virtual_network.get_node(virtual_router)
    #     print(virtual_router.get_name(), "-->", len(virtual_router.get_virtual_interfaces()))

    #     # Now, for each interface in the router, add the route to the routing table
    #     for virtual_interface in virtual_router.get_virtual_interfaces():
    #         # Add the route to the routing table
    #         output = node.cmd(f"ip route add {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} dev {virtual_interface.name}")
    #         if output:
    #             Logger().warning(f"Failed to add route to {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} on {virtual_interface.name}. Error: {output}")
    #         else:
    #             Logger().debug(f"Added route to {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} on {virtual_interface.name}")
    
    Logger().info("Routing tables configured successfully! Starting the Mininet CLI...")
    
    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()
from typing import Optional, cast
from mininet.node import Node
from modules.models.network_elements import (
    NetworkElement,
    Router,
    SwitchInterface,
)
from modules.models.topology import NetworkTopology

from mininet.topo import Topo

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet
from modules.virtualization.network_elements import (
    Gateway,
    Route,
    VirtualHost,
    VirtualNetwork,
    VirtualNetworkInterface,
    VirtualRouter,
    VirtualSwitch,
)
from modules.exploration.explore import RouterPathNode, compute_routers_shortest_path


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd("sysctl net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl net.ipv4.ip_forward=0")
        super(LinuxRouter, self).terminate()


class VirtualNetworkTopology(Topo):
    def is_interface_used(self, element: NetworkElement, interface_name: str, virtual_network: VirtualNetwork) -> bool:
        # Get the virtual router object
        virt_router = virtual_network.get(element.get_name())
        if virt_router is None:
            raise ValueError(
                f"Router {element.get_name()} not found in the virtual network. Are you calling this method after '_link_routers_best_path'?"
            )

        # Check if there is already a virtual interface with the same name
        return any(
            vintf.name == interface_name
            for vintf in virt_router.get_virtual_interfaces()
        )


    def build(self, network: NetworkTopology, virtual_network: VirtualNetwork):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
            network (NetworkTopology): The network topology to virtualize.
        """

        Logger().info("Building the virtual network topology...")

        # First of all, we need to create all network elements
        # 1) Create virtual routers
        for router in network.get_routers():
            # Create the Mininet node describing the router
            self.addHost(
                router.get_name(),
                cls=LinuxRouter,
                ip=None,  # Avoid setting the default IP address
            )
            # Register virtual node in the virtual network object
            virtual_network.add_router(VirtualRouter(router))
        # 2) Create virtual hosts
        for host in network.get_hosts():
            # Create the Mininet node describing the host
            self.addHost(
                host.get_name(),
                ip=None,  # Avoid setting an IP address for now
            )
            # Register virtual node in the virtual network object
            virtual_network.add_host(VirtualHost(host))
        
        # Create mapping between virtual elements and Mininet nodes
        Logger().debug("Creating links between routers...")

        # Compute shortest path between routers
        _, previous = compute_routers_shortest_path(network.get_routers())

        # 1) Connect hosts to routers
        self._link_hosts(network.get_subnets(), virtual_network)

        # 2) Connect routers together using the best possible path
        self._link_routers_best_path(network.get_routers(), previous, virtual_network)

        # 3) Connect routers together using alternative paths (if possible)
        self._link_router_alternative_paths(network.get_routers(), virtual_network)
        
        # 4) Propagate routing tables to all routers in the network
        self._propagate_routes(network.get_routers(), virtual_network)

        # Notify that the topology has been constructed
        Logger().info("The virtual network topology has been built.")

    def _link_routers_best_path(
        self,
        routers: list[Router],
        dijkstra_reverse_graph: dict[Router, Optional[RouterPathNode]],
        virtual_network: VirtualNetwork,
    ):
        """This method connects routers together the best way possible, using the shortest path algorithm.
        This is necessary as we cannot connect the same interface to multiple routers, so we need to find the best way to connect them together.

        Args:
            routers (list[Router]): The list of routers to connect together.
        """
        # Check if we have at least two routers to connect
        if len(routers) < 2:
            return

        # For each router, connect it to the previous one
        # If no previous router found, we can continue to the next one
        for router in routers:
            # Find the best link between this router and the one before
            previous_router_link = dijkstra_reverse_graph.get(router, None)
            if previous_router_link is None:
                continue

            # Create names for the routers interfaces
            src_intf_name = (
                f"{router.get_name()}-{previous_router_link.via_interface.get_name()}"
            )
            dst_intf_name = f"{previous_router_link.router.get_name()}-{previous_router_link.destination_interface.get_name()}"

            # Connect the router to the previous one
            self.addLink(
                router.get_name(),
                previous_router_link.router.get_name(),
                intfName1=src_intf_name,
                params1={"ip": previous_router_link.via_interface.get_ip_with_prefix()},
                intfName2=dst_intf_name,
                params2={
                    "ip": previous_router_link.destination_interface.get_ip_with_prefix()
                },
            )

            # Debug log that the link has been created
            Logger().debug(
                f"\t * created optimal link: {router.get_name()}:{src_intf_name} <--> {previous_router_link.router.get_name()}:{dst_intf_name}"
            )
            Logger().debug(
                f"\t\t IP: {previous_router_link.via_interface.get_ip_with_prefix()} <--> {previous_router_link.destination_interface.get_ip_with_prefix()}"
            )

            # Find the virtual router objects and register the virtual interfaces
            src = virtual_network.get(router.get_name())
            dst = virtual_network.get(previous_router_link.router.get_name())

            # Check if actually they have been created
            if src is None or dst is None:
                raise ValueError(
                    "Virtual routers not found in the virtual network object. This should not happen."
                )

            # Create both virtual iterfaces
            src_vintf = VirtualNetworkInterface(
                name=src_intf_name,
                physical_interface=previous_router_link.via_interface,
            )
            dst_vintf = VirtualNetworkInterface(
                name=dst_intf_name,
                physical_interface=previous_router_link.destination_interface,
            )

            # Register the virtual interfaces used in the link
            src.add_virtual_interface(src_vintf)
            dst.add_virtual_interface(dst_vintf)

            # Set gateway for the source router: any subnet that it cannot reach will be sent to the destination router
            src.set_gateway(
                Gateway(
                    ip=previous_router_link.destination_interface.get_ip(),
                    via_interface_name=src_vintf.name,
                )
            )

            # If the destination router has no gateway, we can setup a fallback gateway to the source router
            # to force this router to use the optimal path even in cases where there are multiple paths to the same destination
            if not dst.get_gateway():
                dst.set_gateway(
                    Gateway(
                        ip=previous_router_link.via_interface.get_ip(),
                        via_interface_name=dst_vintf.name,
                    )
                )

            # Assert that both interfaces are in the same subnet
            assert previous_router_link.via_interface.get_subnet() == previous_router_link.destination_interface.get_subnet()
            subnet = previous_router_link.via_interface.get_subnet()

            # Register the new route for both routers
            src.add_route(
                Route(
                    subnet,
                    src_vintf,
                    dst,
                    dst_vintf,
                )
            )
            dst.add_route(
                Route(
                    subnet,
                    dst_vintf,
                    src,
                    src_vintf,
                )
            )

    def _link_router_alternative_paths(
        self, routers: list[Router], virtual_network: VirtualNetwork
    ):
        # This helper method allows to check if there is already a link that uses the same interface
        # Check if we have at least two routers to connect
        if len(routers) < 2:
            return

        Logger().debug("Creating alternative links between routers...")

        # Create routers for each subnet
        for src_router in routers:
            # Get links to other network elements
            for link in src_router.get_links():
                # Get the link endpoint network element
                dst_router = link.endpoint.entity

                # If it is not a router, we can skip it!
                if not isinstance(dst_router, Router):
                    continue

                # Get the interfaces used in the link
                via_interface = link.interface
                dst_interface = link.endpoint.interface

                # Create names for the routers interfaces
                src_intf_name = f"{src_router.get_name()}-{via_interface.get_name()}"
                dst_intf_name = f"{dst_router.get_name()}-{dst_interface.get_name()}"

                # If any of the interfaces is already used, we can skip this link as it has already been created
                if self.is_interface_used(src_router, src_intf_name, virtual_network) or self.is_interface_used(dst_router, dst_intf_name, virtual_network):
                    continue

                # Connect the router to the previous one
                self.addLink(
                    src_router.get_name(),
                    dst_router.get_name(),
                    intfName1=src_intf_name,
                    params1={"ip": via_interface.get_ip_with_prefix()},
                    intfName2=dst_intf_name,
                    params2={"ip": dst_interface.get_ip_with_prefix()},
                )

                # Debug log that the link has been created
                Logger().debug(
                    f"\t * created alternative link: {src_intf_name} <--> {dst_intf_name}"
                )
                
                Logger().debug(
                    f"\t\t IP: {via_interface.get_ip_with_prefix()} <--> {dst_interface.get_ip_with_prefix()}"
                )

                # Find the virtual router objects and register the virtual interfaces
                src = virtual_network.get(src_router.get_name())
                dst = virtual_network.get(dst_router.get_name())

                # Check if actually they have been created
                if src is None or dst is None:
                    raise ValueError(
                        "Virtual routers not found in the virtual network object. This should not happen."
                    )

                # Create both virtual iterfaces
                src_vintf = VirtualNetworkInterface(
                    name=src_intf_name, physical_interface=via_interface
                )
                dst_vintf = VirtualNetworkInterface(
                    name=dst_intf_name, physical_interface=dst_interface
                )

                # Register the virtual interfaces used in the link
                src.add_virtual_interface(src_vintf)
                dst.add_virtual_interface(dst_vintf)

                # Assert that the subnet is the same for both interfaces
                assert via_interface.get_subnet() == dst_interface.get_subnet()
                subnet = via_interface.get_subnet()

                # Register the route for both routers
                src.add_route(
                    Route(subnet, src_vintf, dst, dst_vintf)
                )
                dst.add_route(
                    Route(subnet, dst_vintf, src, src_vintf)
                )

    def _link_hosts(self, subnets: list[Ipv4Subnet], virtual_network: VirtualNetwork):
        Logger().debug("Creating links between hosts and routers...")

        # counter for switch
        switch_counter = 0

        # Find subnets that interconnect hosts to routers
        for subnet in subnets:
            tot_hosts_endpoints = len(subnet.get_hosts())
            tot_routers_endpoints = len(subnet.get_routers())

            # If there are no hosts, this means that this subnet is used between routers. We can ignore it.
            if tot_hosts_endpoints == 0:
                continue

            # Now that we have found a valid subnet, we must ensure that there is a router connected to it
            if tot_routers_endpoints == 0:
                hosts = " ,".join(
                    [host.entity.get_name() for host in subnet.get_hosts()]
                )
                Logger().warning(
                    f"No router present in subnet {subnet.network_address()}/{subnet.get_prefix_length()}. The following hosts will not be connected: {hosts}"
                )

            # Now, if we have only one host, we can connect it directly to the router without a switch
            if tot_hosts_endpoints == 1 and tot_routers_endpoints == 1:
                # Connect router directly to single host
                host_endpoint = subnet.get_hosts()[0]
                router_endpoint = subnet.get_routers()[0]

                Logger().debug(
                    f"Connecting {host_endpoint.entity.get_name()}:{host_endpoint.interface.get_name()} directly to {router_endpoint.entity.get_name()}:{router_endpoint.interface.get_name()} in subnet {subnet.network_address()}/{subnet.get_prefix_length()}..."
                )

                # Create interface names
                host_intf_name = f"{host_endpoint.entity.get_name()}-{host_endpoint.interface.get_name()}"
                router_intf_name = f"{router_endpoint.entity.get_name()}-{router_endpoint.interface.get_name()}"

                Logger().debug(
                    f"Connecting host {host_endpoint.entity.get_name()}:{host_endpoint.interface.get_name()} to router {router_endpoint.entity.get_name()}:{router_endpoint.interface.get_name()}..."
                )
                
                # Add link between host and router
                self.addLink(
                    host_endpoint.entity.get_name(),
                    router_endpoint.entity.get_name(),
                    intfName1=host_intf_name,
                    params1={"ip": host_endpoint.interface.get_ip_with_prefix()},
                    intfName2=router_intf_name,
                    params2={"ip": router_endpoint.interface.get_ip_with_prefix()},
                )

                Logger().debug(
                    f"\t * created link: {host_intf_name} <--> {router_intf_name}"
                )

                # Register the virtual interfaces
                host = virtual_network.get(host_endpoint.entity.get_name())
                router = virtual_network.get(router_endpoint.entity.get_name())

                # Check if actually they have been created
                if host is None or router is None:
                    raise ValueError(
                        "Virtual host or router not found in the virtual network object. This should not happen."
                    )

                # Create both virtual iterfaces
                host_vintf = VirtualNetworkInterface(
                    name=host_intf_name, physical_interface=host_endpoint.interface
                )
                router_vintf = VirtualNetworkInterface(
                    name=router_intf_name, physical_interface=router_endpoint.interface
                )

                # Register the virtual interfaces used in the link
                host.add_virtual_interface(host_vintf)
                router.add_virtual_interface(router_vintf)

                # Register route in router
                router.add_route(
                    Route(
                        host_endpoint.interface.get_subnet(),
                        router_vintf,
                        host,
                        host_vintf,
                    )
                )

                # Add default gateway for the host
                host.set_gateway(
                    Gateway(
                        ip=router_endpoint.interface.get_ip(),
                        via_interface_name=router_intf_name,
                    )
                )
            else:
                # We create a switch to connect multiple hosts to the router
                switch = self.addSwitch(f"s{switch_counter}", ip=None)
                switch_counter += 1

                # Counter for network interfaces for this particular switch
                switch_intf_counter = 0

                # Create virtual switch object
                virt_switch = VirtualSwitch(
                    NetworkElement(
                        name=switch,
                    )
                )
                virtual_network.add_switch(virt_switch)

                # Now, for each host, we connect it to the switch
                for host in subnet.get_hosts():
                    # Create interface names
                    host_intf_name = (
                        f"{host.entity.get_name()}-{host.interface.get_name()}"
                    )
                    switch_intf_name = f"{switch}-eth{switch_intf_counter}"

                    Logger().debug(
                        f"Connecting host {host.entity.get_name()}:{host.interface.get_name()} to switch {switch}:eth{switch_intf_counter}..."
                    )

                    # Increment the counter for the switch interface
                    switch_intf_counter += 1


                    # Add link between host and switch
                    self.addLink(
                        host.entity.get_name(),
                        switch,
                        intfName1=host_intf_name,
                        params1={"ip": host.interface.get_ip_with_prefix()},
                        intfName2=switch_intf_name,  # No ip needed for the switch!
                    )

                    Logger().debug(
                        f"\t * created link: {host_intf_name} to switch {switch}"
                    )

                    # Register the virtual interfaces
                    virt_host = virtual_network.get(host.entity.get_name())

                    # Check if actually they have been created
                    if virt_host is None:
                        raise ValueError(
                            "Virtual host or switch not found in the virtual network object. This should not happen."
                        )

                    # Create both virtual iterfaces
                    host_vintf = VirtualNetworkInterface(
                        name=host_intf_name, physical_interface=host.interface
                    )

                    # Register the virtual interfaces used in the link
                    virt_host.add_virtual_interface(host_vintf)

                # Now, we need also to connect the switch to the routers of the subnet
                for router in subnet.get_routers():
                    # Create interface names
                    router_intf_name = (
                        f"{router.entity.get_name()}-{router.interface.get_name()}"
                    )
                    switch_intf_name = f"{switch}-eth{switch_intf_counter}"

                    Logger().debug(
                        f"Connecting router {router.entity.get_name()}:{router.interface.get_name()} to switch {switch}:eth{switch_intf_counter}..."
                    )

                    # Increment the counter for the switch interface
                    switch_intf_counter += 1

                    # Add link between switch and router
                    self.addLink(
                        router.entity.get_name(),
                        switch,
                        # Configure link between router and switch
                        intfName1=router_intf_name,
                        params1={"ip": router.interface.get_ip_with_prefix()},
                        intfName2=switch_intf_name,  # No ip needed for the switch!
                    )

                    Logger().debug(
                        f"\t * created link: switch {switch} to router {router_intf_name}"
                    )

                    # Register the virtual interfaces
                    virt_router = virtual_network.get(router.entity.get_name())

                    # Check if actually they have been created
                    if virt_router is None:
                        raise ValueError(
                            "Virtual router or switch not found in the virtual network object. This should not happen."
                        )

                    # register the virtual interface
                    router_vintf = VirtualNetworkInterface(
                        name=router_intf_name, physical_interface=router.interface
                    )

                    # Register the virtual interfaces used in the link
                    virt_router.add_virtual_interface(router_vintf)

                    # Register route to this subnet in the router via the switch interface
                    virt_router.add_route(
                        Route(
                            subnet,
                            router_vintf,
                            virt_switch,
                            VirtualNetworkInterface(
                                name=switch_intf_name,
                                physical_interface=SwitchInterface(switch_intf_name),
                            ),
                        )
                    )

                # Set hosts default gateway to the first router in the subnet
                first_router = subnet.get_routers()[0]
                for host in subnet.get_hosts():
                    # Get the virtual host object
                    virt_host = virtual_network.get(host.entity.get_name())
                    if virt_host is None:
                        raise ValueError(
                            f"Virtual host {host.entity.get_name()} not found in the virtual network. There is a problem with the network topology."
                        )

                    # Set the default gateway for the host
                    virt_host.set_gateway(
                        Gateway(
                            ip=first_router.interface.get_ip(),
                            via_interface_name=f"{switch}-eth0",
                        )
                    )

    def _propagate_routes(self, routers: list[Router], virtual_network: VirtualNetwork):
        Logger().debug("Propagating routing information to routers...")

        def _get_virtual_router(router: Router) -> VirtualRouter:
            virt_router = virtual_network.get(router.get_name())
            if virt_router is None:
                raise ValueError(
                    f"Router {src_router.get_name()} not found in the virtual network. Are you calling this method after '_link_routers_best_path'?"
                )
            return cast(VirtualRouter, virt_router)

        # For each router, print its routes
        for src_router in routers:
            # Get the virtual router object
            src_virtual_router = _get_virtual_router(src_router)

            # Identify all the routes that can be reached from this router from the routes
            routes_to_routers = [
                route
                for route in src_virtual_router.get_routes()
                if isinstance(route.to_element, VirtualRouter)
            ]

            # For each destination router, we need to propagate the routes that can be reached only from the src_router and not from the dst_router
            for route_to_router in routes_to_routers:
                # Identify routes that are not present in the router we are propagating the routes to
                router_target = route_to_router.to_element

                # Identify also the routes we need to propagate to the target router
                dst_missing_routes = list[Route]()
                for route in src_virtual_router.get_routes():
                    for dst_route in router_target.get_routes():
                        if route.subnet == dst_route.subnet:
                            break
                    else:
                        dst_missing_routes.append(route)

                # Find all possible routes from src_router to router_target in order to have the correct "via interface" for the missing routes
                possible_routes = list[Route]()
                for route in router_target.get_routes():
                    if route.to_element == src_virtual_router:
                        possible_routes.append(route)

                # We need to add the missing routes to the destination router BUT we need to change the "via interface" to the one that connects dst_router to src_router via the link
                for dst_missing_route in dst_missing_routes:
                    # We need to update the missing route to match the target router configuration
                    # In addition, if we have multiple routes between the routers, we add multiple route entries in order to provide failover capabilities
                    for possible_route in possible_routes:
                        # Create the new route
                        new_route = Route(
                            subnet=dst_missing_route.subnet,
                            via_interface=possible_route.via_interface,
                            to_element=src_virtual_router,
                            dst_interface=possible_route.dst_interface,
                            is_registered=False,  # Flag this route as not registered (we need to add it to the routing table manually)
                        )
                        # Register the new route in the target router
                        router_target.add_route(new_route)

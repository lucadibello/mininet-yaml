from typing import Optional, cast
from modules.models.network_elements import Router, NetworkInterface, NetworkElement

from mininet.node import Node
from mininet.net import Mininet

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet


class VirtualNetworkInterface:
    def __init__(self, name: str, physical_interface: NetworkInterface, is_blacklisted: bool = False):
        self._name = name
        self._physical_interface = physical_interface
        self._is_blacklisted = is_blacklisted
    @property
    def name(self) -> str:
        return self._name

    @property
    def physical_interface(self) -> NetworkInterface:
        return self._physical_interface
    
    @property
    def is_blacklisted(self) -> bool:
        return self._is_blacklisted
    
    def flag_blacklisted(self):
        self._is_blacklisted = True
    
    def clear_blacklisted_flag(self):
        self._is_blacklisted = False
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VirtualNetworkInterface):
            return False
        return self.name == other.name and self.physical_interface == other.physical_interface
    
    def __hash__(self) -> int:
        return hash((self.name, self.physical_interface))


class Gateway:
    def __init__(self, ip: str, via_interface_name: str):
        self._interface = via_interface_name
        self._ip = ip

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def interface(self) -> str:
        return self._interface


class VirtualNetworkElement:
    def __init__(self, physical_element: NetworkElement):
        self._physical_element = physical_element
        self._virtual_interfaces = list[VirtualNetworkInterface]()
        self._gateway: Optional[Gateway] = None
        self._routes = list[Route]()

    def get_name(self) -> str:
        return self._physical_element.get_name()

    def get_physical_element(self) -> NetworkElement:
        return self._physical_element

    def add_virtual_interface(self, interface: VirtualNetworkInterface):
        self._virtual_interfaces.append(interface)

    def get_virtual_interfaces(self) -> list[VirtualNetworkInterface]:
        return self._virtual_interfaces

    def set_gateway(self, gateway: Gateway):
        self._gateway = gateway

    def get_gateway(self) -> Optional[Gateway]:
        return self._gateway

    def add_route(self, route: "Route"):
        self._routes.append(route)

    def get_routes(self) -> list["Route"]:
        return self._routes
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VirtualNetworkElement):
            return False
        return self.get_name() == other.get_name() and self.get_physical_element() == other.get_physical_element()

    def __hash__(self) -> int:
        return hash((self.get_name(), self.get_physical_element()))


#
# Specialized classes for (possible) future extensions
#


class VirtualRouter(VirtualNetworkElement):
    def __init__(self, physical_router: Router):
        super().__init__(physical_router)


class VirtualHost(VirtualNetworkElement):
    def __init__(self, physical_host: NetworkElement):
        super().__init__(physical_host)


class VirtualSwitch(VirtualNetworkElement):
    def __init__(self, physical_switch: NetworkElement):
        super().__init__(physical_switch)


class VirtualNetwork:
    def __init__(self):
        self._virtual_routers = list[VirtualRouter]()
        self._virtual_hosts = list[VirtualHost]()
        self._virtual_switches = list[VirtualNetworkElement]()
        self._net: Optional[Mininet] = None

        # Link between physical and virtual network elements
        self._virtual_physical_links = dict[str, VirtualNetworkElement]()

    def has(self, element: NetworkElement) -> bool:
        return element.get_name() in self._virtual_physical_links

    def set_network(self, net: Mininet):
        self._net = net

    def get(self, name: str) -> Optional[VirtualNetworkElement]:
        return self._virtual_physical_links.get(name, None)

    def get_mininet_node(self, virtual_element: VirtualNetworkElement) -> Node:
        if not self._net:
            raise ValueError(
                "The virtual network has not been linked to the Mininet instance yet!"
            )
        # Force type cast to Node (Mininet node)
        return cast(Node, self._net.get(virtual_element.get_name()))

    def add_switch(self, switch: VirtualSwitch):
        self._virtual_physical_links[switch.get_name()] = switch
        self._virtual_switches.append(switch)

    def add_router(self, router: VirtualRouter):
        self._virtual_physical_links[router.get_name()] = router
        self._virtual_routers.append(router)

    def add_host(self, host: VirtualHost):
        self._virtual_physical_links[host.get_name()] = host
        self._virtual_hosts.append(host)

    def get_routers(self) -> list[VirtualRouter]:
        return self._virtual_routers

    def get_hosts(self) -> list[VirtualHost]:
        return self._virtual_hosts

    def get_switches(self) -> list[VirtualNetworkElement]:
        return self._virtual_switches
    
    def propagate_routes(self):
        Logger().debug("Propagating routing information to routers...")
        for src_virtual_router in self.get_routers():
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


class Route:
    def __init__(
        self,
        subnet: Ipv4Subnet,
        via_interface: VirtualNetworkInterface,
        to_element: VirtualNetworkElement,
        dst_interface: VirtualNetworkInterface,
        is_registered=True,
    ) -> None:
        self._subnet = subnet
        self._via_interface = via_interface
        self._to_element = to_element
        self._dst_interface = dst_interface
        self._is_registered = is_registered

        # Keep track of optional maker
        self._marker = None

    @property
    def subnet(self) -> Ipv4Subnet:
        return self._subnet

    @property
    def via_interface(self) -> VirtualNetworkInterface:
        return self._via_interface

    @property
    def to_element(self) -> VirtualNetworkElement:
        return self._to_element

    @property
    def dst_interface(self) -> VirtualNetworkInterface:
        return self._dst_interface

    @property
    def is_registered(self) -> bool:
        return self._is_registered
    
    @property
    def marker(self) -> Optional[int]:
        return self._marker
    
    def set_marker(self, marker: int):
        self._marker = marker
        

    def reverse(self, new_dst_element: VirtualNetworkElement) -> "Route":
        """
        This method allows to easily reverse the route, requiring to define the new destination element.
        """
        return Route(
            self._subnet,
            self._dst_interface,
            new_dst_element,
            self._via_interface,
            is_registered=False,
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Route):
            return False
        return (
            self._via_interface == other.via_interface
            and self._to_element == other.to_element
            and self._dst_interface == other.dst_interface
        )
    
    def __hash__(self) -> int:
        return hash((self._via_interface, self._to_element, self._dst_interface))

    def __str__(self) -> str:
        return f"Route for {self._subnet} available by exiting on intf {self._via_interface.name} (ip: {self._via_interface.physical_interface.get_ip()}) and, and reaching {self._to_element.get_name()} on interface {self._dst_interface.name} (ip: {self._dst_interface.physical_interface.get_ip()})"

from typing import Optional, TypedDict, cast
from modules.models.network_elements import Router, NetworkInterface, NetworkElement

from mininet.node import Node
from mininet.net import Mininet

from modules.util.network import Ipv4Subnet

class VirtualNetworkInterface():
    def __init__(self, name: str, physical_interface: NetworkInterface):
        self._name = name
        self._physical_interface = physical_interface

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def physical_interface(self) -> NetworkInterface:
        return self._physical_interface

class Gateway():
    def __init__(self, ip: str, via_interface_name: str):
        self._interface = via_interface_name
        self._ip = ip
    
    @property
    def ip(self) -> str:
        return self._ip
    @property
    def interface(self) -> str:
        return self._interface

class VirtualNetworkElement():
    def __init__(self, physical_element: NetworkElement):
        self._physical_element = physical_element
        self._virtual_interfaces = list[VirtualNetworkInterface]()
        self._gateway: Optional[Gateway] = None
        self._routes = list[tuple[Ipv4Subnet, VirtualNetworkInterface]]()
    
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

    def add_route(self, subnet: Ipv4Subnet, interface: VirtualNetworkInterface):
        self._routes.append((subnet, interface))

    def get_routes(self) -> list[tuple[Ipv4Subnet, VirtualNetworkInterface]]:
        return self._routes

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
            raise ValueError("The virtual network has not been linked to the Mininet instance yet!")
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
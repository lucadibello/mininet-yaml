from typing import Optional, cast
from modules.models.network_elements import Router, NetworkInterface, NetworkElement

from mininet.node import Node
from mininet.net import Mininet

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


class VirtualNetworkElement():
    def __init__(self, physical_element: NetworkElement):
        self._physical_element = physical_element
        self._virtual_interfaces = list[VirtualNetworkInterface]()
    
    def get_name(self) -> str:
        return self._physical_element.get_name()

    def get_physical_element(self) -> NetworkElement:
        return self._physical_element
    
    def add_virtual_interface(self, interface: VirtualNetworkInterface):
        self._virtual_interfaces.append(interface)
    
    def get_virtual_interfaces(self) -> list[VirtualNetworkInterface]:
        return self._virtual_interfaces

class VirtualRouter(VirtualNetworkElement):
    def __init__(self, physical_router: Router):
        super().__init__(physical_router)
    
class VirtualHost(VirtualNetworkElement):
    def __init__(self, physical_host: NetworkElement):
        super().__init__(physical_host)
        
class VirtualNetwork:
    def __init__(self):
        self._virtual_routers = list[VirtualRouter]()
        self._virtual_hosts = list[VirtualHost]()
        self._virtual_switches = list[VirtualNetworkElement]()
        self._net: Optional[Mininet] = None
        
    def set_network(self, net: Mininet):
        self._net = net

    def get_node(self, virtual_element: VirtualNetworkElement) -> Node:
        if not self._net:
            raise ValueError("The virtual network has not been linked to the Mininet instance yet!")
        # Force type cast to Node (Mininet node)
        return cast(Node, self._net.get(virtual_element.get_name()))

    def add_virtual_switch(self, switch: VirtualNetworkElement):
        self._virtual_switches.append(switch)
    
    def add_virtual_router(self, router: VirtualRouter):
        self._virtual_routers.append(router)
    
    def get_virtual_routers(self) -> list[VirtualRouter]:
        return self._virtual_routers

    def add_virtual_host(self, host: VirtualHost):
        self._virtual_hosts.append(host)

    def get_virtual_switches(self) -> list[VirtualNetworkElement]:
        return self._virtual_switches
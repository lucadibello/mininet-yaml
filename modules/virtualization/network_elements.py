from modules.models.network_elements import Router, NetworkInterface, NetworkElement
from modules.util.network import Ipv4Subnet

class VirtualNetworkElement():
    def __init__(self, name: str, physical_element: NetworkElement):
        self._name = name
        self._physical_element = physical_element
    
    def get_name(self) -> str:
        return self._name

    def get_physical_element(self) -> NetworkElement:
        return self._physical_element

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

class VirtualRouter(VirtualNetworkElement):
    
    def __init__(self, name: str, physical_router: Router):
        super().__init__(name, physical_router)
        self._virtual_interfaces = list[VirtualNetworkInterface]()
    
    def add_virtual_interface(self, interface: VirtualNetworkInterface):
        self._virtual_interfaces.append(interface)
    
    def get_virtual_interfaces(self) -> list[VirtualNetworkInterface]:
        return self._virtual_interfaces

class VirtualHost(VirtualNetworkElement):
    
    def __init__(self, name: str, physical_host: NetworkElement):
        super().__init__(name, physical_host)
        
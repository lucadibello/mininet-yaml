from typing import Sequence
from modules.models.network_elements import Host, Link, NetworkElement, NetworkInterface, Router

class Ipv4Network:
    def __init__(self, ip: str, mask: str):
        self._ip = ip
        self._mask = mask

    def get_ip(self) -> str:
        """
        This method returns the IP address of the subnet.
        """
        return self._ip
    def get_mask(self) -> str:
        """
        This method returns the subnet mask of the subnet.
        """
        return self._mask

    def to_binary(self) -> str:
        """
        This method converts the IPv4 network to its binary representation.
        """
        return "".join([bin(int(x) + 256)[3:] for x in self._ip.split(".")])

    def network_address(self) -> str:
        """
        This method returns the network address of the IPv4 network by applying the subnet mask.
        """
        return ".".join(
            str(int(x) & int(y))
            for x, y in zip(self._ip.split("."), self._mask.split("."))
        )

    @staticmethod
    def can_communicate(a: "Ipv4Network", b: "Ipv4Network") -> bool:
        """
        This method checks if two IPv4 addresses can communicate with each other.
        """
        return a.network_address() == b.network_address()

class Ipv4Subnet(Ipv4Network):
    def __init__(self, ip: str, mask: str):
        # Construct the Ipv4Network object
        super().__init__(ip, mask)
        # Initialize the list of clients that are part of this subnet
        self._hosts = list[Link.Endpoint]()
        self._routers = list[Link.Endpoint]()

    @staticmethod
    def create_from(local_ip: str, mask: str) -> "Ipv4Subnet":
        """
        This method creates an Ipv4Subnet object from a NetworkInterface object.
        """
        return Ipv4Subnet(Ipv4Network(local_ip, mask).network_address(), mask) 
    
    def add_host(self, host_endpoint: Link.Endpoint):
        """
        Host method adds an Host to the subnet.
        """
        self._hosts.append(host_endpoint)

    def add_router(self, router_endpoint: Link.Endpoint):
        """
        This method adds a Router to the subnet.
        """
        self._routers.append(router_endpoint)

    def get_clients(self) -> list[Link.Endpoint]:
        """
        This method returns the list of clients that are part of this subnet.
        """
        return self._hosts + self._routers
    
    def get_hosts(self) -> list[Link.Endpoint]:
        """
        This method returns the list of hosts that are part of this subnet.
        """
        return self._hosts

    def get_routers(self) -> list[Link.Endpoint]:
        """
        This method returns the list of routers that are part of this subnet.
        """
        return self._routers
    
    def get_prefix_length(self) -> int:
        return sum([bin(int(x)).count('1') for x in self._mask.split('.')])
    
    def get_next_management_ip(self) -> str:
        """
        This method returns the next available IP address for management.
        """
        def get_last_octet(ip: str) -> int:
            return int(ip.split(".")[-1])
        
        # Starting from .254, find the first available IP address
        for i in range(254, 0, -1):
            ip = f"{self.network_address()[0:self.network_address().rfind('.')]}.{i}"
            if not any(get_last_octet(client.interface.get_ip()) == i for client in self.get_clients()):
                return ip
        raise ValueError("No available IP addresses for management")

    def __str__(self) -> str:
        return f"{self._ip}/{self._mask}, Clients: {', '.join([client.entity.get_name() for client in self.get_clients()])}"

    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ipv4Subnet):
            return False
        return self._ip == other._ip and self._mask == other._mask


def does_link_exist(
        a: NetworkElement, b: NetworkElement
) -> tuple[bool, list[tuple[NetworkInterface, NetworkInterface]]]:
    """
    This function checks if two network elements are linked together in the network topology.

    Parameters:
    a (NetworkElement): The first network element.
    b (NetworkElement): The second network element.

    Returns:
    tuple[bool, list[tuple[NetworkInterface, NetworkInterface]]: A tuple containing a boolean value indicating if the link exists and a list of tuples containing the interfaces that are linked.
    """
    linked_interfaces = []

    # For each interface of each network element, create an Ipv4Network object
    for interface_a in a.get_interfaces():
        network_a = Ipv4Network(interface_a.get_ip(), interface_a.get_mask())

        for interface_b in b.get_interfaces():
            network_b = Ipv4Network(
                interface_b.get_ip(), interface_b.get_mask())

            # Ensure that both networks can communicate with each other
            if Ipv4Network.can_communicate(network_a, network_b):
                # If they overlap, it means the interfaces are linked
                linked_interfaces.append((interface_a, interface_b))

    # If linked_interfaces is not empty, then a link exists
    link_exists = len(linked_interfaces) > 0
    return link_exists, linked_interfaces

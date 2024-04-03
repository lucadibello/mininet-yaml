from typing import Sequence
from modules.util.logger import Logger
from modules.util.network import Ipv4Network


def _does_link_exist(
    a: "NetworkElement", b: "NetworkElement"
) -> tuple[bool, list[tuple["NetworkInterface", "NetworkInterface"]]]:
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
            network_b = Ipv4Network(interface_b.get_ip(), interface_b.get_mask())

            # Ensure that both networks can communicate with each other
            if Ipv4Network.can_communicate(network_a, network_b):
                # If they overlap, it means the interfaces are linked
                linked_interfaces.append((interface_a, interface_b))

    # If linked_interfaces is not empty, then a link exists
    link_exists = len(linked_interfaces) > 0
    return link_exists, linked_interfaces


class NetworkInterface:
    """
    This class represents a network interface of a network element.
    """

    def __init__(self, name: str, ip: str, mask: str):
        self._name = name
        self._ip = ip
        self._mask = mask

    def get_name(self):
        return self._name

    def get_ip(self):
        return self._ip

    def get_mask(self):
        return self._mask

    def __str__(self):
        return f"Interface(name={self._name}, subnet=({self._ip}/{self._mask}))"

    def __repr__(self):
        return self.__str__()


class RouterNetworkInterface(NetworkInterface):
    """
    This class represents a network interface of a router.
    """

    def __init__(self, name: str, ip: str, mask: str, cost: int = 1):
        super().__init__(name, ip, mask)
        self._cost = cost

    def __str__(self):
        return f"Interface(name={self._name}, subnet=({self._ip}/{self._mask}), cost={self._cost})"

    def __repr__(self):
        return self.__str__()


class NetworkElement:
    """
    This class represents a network element (router/host) in the network topology.
    """

    def __init__(self, name: str):
        self._name = name
        self._interfaces: list[NetworkInterface] = []
        self._links: list[tuple[NetworkElement, NetworkInterface]] = []

    def set_interfaces(self, interfaces: list[NetworkInterface]):
        self._interfaces = interfaces

    def add_interface(self, interface: NetworkInterface):
        self._interfaces.append(interface)

    def get_interfaces(self):
        return self._interfaces

    def set_name(self, name: str):
        self._name = name

    def get_name(self):
        return self._name

    def add_link(self, link: tuple["NetworkElement", NetworkInterface]):
        self._links.append(link)

    def get_links(self):
        return self._links


class Router(NetworkElement):
    """
    This class represents a router in the network topology.
    """

    def __init__(self, name: str, interfaces: list[RouterNetworkInterface] = []):
        super().__init__(name)
        # Add one interface at the time to allow casting to the correct type
        for interface in interfaces:
            self.add_interface(interface)

    def __str__(self):
        return f"Router(name={self.get_name()}, interfaces={self.get_interfaces()})"

    def __repr__(self):
        return self.__str__()


class Host(NetworkElement):
    """
    This class represents a host in the network topology.
    """

    def __init__(self, name: str, interfaces: list[NetworkInterface] = []):
        super().__init__(name)
        for interface in interfaces:
            self.add_interface(interface)

    def __str__(self):
        return f"Host(name={self.get_name()}, interfaces={self.get_interfaces()})"

    def __repr__(self):
        return self.__str__()


class NetworkTopology:
    """
    This class represents the network topology of the virtual network
    """

    def __init__(self, routers: list[Router], hosts: list[Host]):
        self._routers = routers
        self._hosts = hosts

        _total_links = 0

        # Find and create all the links between routers and hosts
        _total_links += NetworkTopology._create_links(self._routers, self._hosts)
        # Find links between routers
        _total_links += NetworkTopology._create_links(self._routers, self._routers)
        # Find links between hosts
        _total_links += NetworkTopology._create_links(self._hosts, self._hosts)

        # Check if there are some network elements that are not linked to any other network element
        for router in self._routers:
            if not router.get_links():
                Logger().warning(
                    f"Router {router.get_name()} is not linked to any other network element."
                )
        for host in self._hosts:
            if not host.get_links():
                Logger().warning(
                    f"Host {host.get_name()} is not linked to any other network element."
                )

        # Save total number of unique links
        self._total_links = _total_links

    @staticmethod
    def _create_links(
        set_a: Sequence["NetworkElement"], set_b: Sequence["NetworkElement"]
    ) -> int:
        # Find all the links between routers and hosts
        total_links = 0
        for a in set_a:
            for b in set_b:
                # If for any reason the two network elements are the same, skip as they cannot be linked
                if a.get_name() == b.get_name():
                    continue

                # Compute all possible links between the two network elements
                found, interfaces = _does_link_exist(a, b)
                if not found:
                    continue

                # Add the link between the two elements
                for source_interface, destination_interface in interfaces:
                    total_links += 1
                    a.add_link((b, source_interface))
                    b.add_link((a, destination_interface))

        # Return total amount of unique links
        return total_links

    def __str__(self):
        return f"NetworkTopology(routers={self._routers}, hosts={self._hosts})"

    def __repr__(self):
        return self.__str__()

    def get_routers(self):
        return self._routers

    def get_hosts(self):
        return self._hosts

    def get_total_links(self):
        return self._total_links

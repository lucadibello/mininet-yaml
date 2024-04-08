from modules.models.network_elements import NetworkElement, NetworkInterface


class Ipv4Network:
    def __init__(self, ip: str, mask: str):
        self._ip = ip
        self._mask = mask

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
        self._clients = []

    def add_client(self, client: NetworkElement):
        """
        This method adds a client to the subnet.
        """
        self._clients.append(client)

    def get_clients(self) -> list[NetworkElement]:
        """
        This method returns the list of clients that are part of this subnet.
        """
        return self._clients

    def __str__(self) -> str:
        return f"{self._ip}/{self._mask}, Clients: {', '.join([client.get_name() for client in self._clients])}"

    def __repr__(self) -> str:
        return self.__str__()


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

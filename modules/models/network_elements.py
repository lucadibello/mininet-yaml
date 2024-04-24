# Constants
_DEFAULT_COST = 1
_DEFAULT_DEMAND_RATE = 0

class NetworkInterface:
    """
    This class represents a network interface of a network element.
    """

    def __init__(self, name: str, ip: str, mask: str):
        self._name = name
        self._ip = ip
        self._mask = mask
        # Import required modules
        from modules.util.network import Ipv4Subnet

        # Create the subnet if the IP and mask are provided
        if ip and mask:
            self._subnet = Ipv4Subnet.create_from(ip, mask)
        # Flag that indicates if the interface is used
        self._used = False

    def get_name(self):
        return self._name

    def get_ip(self):
        return self._ip

    def get_mask(self):
        return self._mask

    def get_prefix_length(self):
        return self._subnet.get_prefix_length()

    def get_ip_with_prefix(self):
        return self._ip + "/" + str(self.get_prefix_length())

    def get_subnet(self):
        return self._subnet

    def is_used(self):
        return self._used

    def set_used(self, used: bool):
        self._used = used

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, NetworkInterface):
            return False
        return (
            self._name == value._name
            and self._ip == value._ip
            and self._mask == value._mask
        )

    def __str__(self):
        return f"Interface(name={self._name}, subnet=({self._ip}/{self._mask}))"

    def __repr__(self):
        return self.__str__()


class SwitchInterface(NetworkInterface):
    """
    This class represents a network interface of a switch.
    """

    def __init__(self, name: str):
        super().__init__(name, "", "")


class RouterNetworkInterface(NetworkInterface):
    """
    This class represents a network interface of a router.
    """

    def __init__(self, name: str, ip: str, mask: str, cost: int = _DEFAULT_COST):
        super().__init__(name, ip, mask)
        self._cost = cost

    def __str__(self):
        return f"Interface(name={self._name}, subnet=({self._ip}/{self._mask}), cost={self._cost})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, RouterNetworkInterface):
            return False
        return super().__eq__(value) and self._cost == value._cost

    def get_cost(self):
        return self._cost

    def set_cost(self, cost: int):
        self._cost = cost


class Link:
    class Endpoint:
        """
        This class represents an endpoint of a link. It contains the network element and the interface.
        """

        def __init__(
            self, entity: "NetworkElement", interface: NetworkInterface
        ) -> None:
            self._entity = entity
            self._interface = interface

        def __eq__(self, value: object) -> bool:
            if not isinstance(value, Link.Endpoint):
                return False
            return self.entity == value.entity and self.interface == value.interface

        @property
        def entity(self):
            return self._entity

        @property
        def interface(self):
            return self._interface

    def __init__(self, source_interface: NetworkInterface, destination: Endpoint):
        self._interface = source_interface
        self._endpoint = destination

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Link):
            return False
        return self.interface == value.interface and self.endpoint == value.endpoint

    @property
    def interface(self):
        return self._interface

    @property
    def endpoint(self):
        return self._endpoint


class NetworkElement:
    """
    This class represents a network element (router/host) in the network topology.
    """

    def __init__(self, name: str):
        self._name = name
        self._interfaces: list[NetworkInterface] = []
        self._links: list[Link] = []
        self._demands: list[NetworkElementDemand] = []

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

    def has_link(self, link: Link):
        for l in self._links:
            if l.interface == link.interface and l.endpoint == link.endpoint:
                return True
        return False

    def add_link(self, link: Link):
        self._links.append(link)

    def get_links(self):
        return self._links

    def get_demands(self):
        return self._demands
    
    def add_demand(self, demand: "NetworkElementDemand"):
        self._demands.append(demand)

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

class NetworkElementDemand:
    """
    This class represents a minimum transmission rate demand between the current network element and another one
    """

    def __init__(
        self,
        destination: NetworkElement,
        transmissionRateDemand: int = _DEFAULT_DEMAND_RATE,
    ):
        self._destination = destination
        self._demandTransmissionRate = transmissionRateDemand


class Demand(NetworkElementDemand):
    """
    This class represents a minimum transmission rate demand between two network elements.
    """

    def __init__(
        self,
        source: NetworkElement,
        destination: NetworkElement,
        transmissionRateDemand: int = _DEFAULT_DEMAND_RATE,
    ):
        super().__init__(destination, transmissionRateDemand)
        self._source = source

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def demandTransmissionRate(self):
        return self._demandTransmissionRate

    def __str__(self) -> str:
        return f"Demand(source={self.source.get_name()}, destination={self.destination.get_name()}, transmissionRateBytes={self.demandTransmissionRate})"

    def __repr__(self) -> str:
        return self.__str__()

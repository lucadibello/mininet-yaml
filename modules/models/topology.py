class NetworkInterface:
    """
    This class represents a network interface of a network element.
    """

    def __init__(self, name: str, ip: str, mask: str):
        self._name = name
        self._ip = ip
        self._mask = mask

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
        self.set_interfaces(interfaces)

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

    def __str__(self):
        return f"NetworkTopology(routers={self._routers}, hosts={self._hosts})"

    def __repr__(self):
        return self.__str__()

    def get_routers(self):
        return self._routers

    def get_hosts(self):
        return self._hosts

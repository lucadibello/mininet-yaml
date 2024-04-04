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

	def get_cost(self):
		return self._cost


class Link:
	"""
	This class represents a link between two network interfaces.
	"""

	class Endpoint():
		"""
		This class represents an endpoint of a link. It contains the network element and the interface.
		"""
		def __init__(self, entity: "NetworkElement", interface: NetworkInterface) -> None:
			self._entity = entity
			self._interface = interface
		
		@property
		def entity(self):
			return self._entity
		
		@property
		def interface(self):
			return self._interface

	def __init__(self, source: Endpoint, destination: Endpoint):
		self._source = source
		self._destination = destination

	def get_source(self):
		return self._source

	def get_destination(self):
		return self._destination

	def __str__(self):
		return f"Link(source={self._source}, destination={self._destination})"

	def __repr__(self):
		return self.__str__()


class NetworkElement:
	"""
	This class represents a network element (router/host) in the network topology.
	"""

	def __init__(self, name: str):
		self._name = name
		self._interfaces: list[NetworkInterface] = []
		self._links: list[Link] = []

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

	def add_link(self, link: Link):
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


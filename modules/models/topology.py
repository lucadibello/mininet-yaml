from operator import index
from typing import Sequence, TypedDict, cast
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

					# Create link between the two network elements
					link = Link(
						source=Link.Endpoint(entity=a, interface=source_interface),
						destination=Link.Endpoint(
							entity=b, interface=destination_interface
						),
					)

					# Add the link to the source network element
					a.add_link(link)

		# Return total amount of unique links
		return total_links

	def draw(self):
		"""
		This method returns a string containing a GraphViz representation of the network topology.
		It includes only Routers and shows the cost of the links between them.
		"""
		graph = "graph network {\n"

		# Total number of routers
		tot_routers = len(self._routers)

		# Sort the routers by name to keep the indexing consistent
		self._routers.sort(key=lambda x: x.get_name())

		# Create hashmap to get the index of a router by its name in O(1)
		router_index = {router.get_name(): index for index, router in enumerate(self._routers)}

		# 3D adjacency matrix to store the edges between routers, and cost of the link between them
		adj_matrix: list[list[list[int]]] = [[list() for _ in range(tot_routers)] for _ in range(tot_routers)]

		def _print_matrix(matrix):
			for row in matrix:
				print(row)
	
		def get_index(router):
			return router_index[router.get_name()]	

		# Created nodes for each router
		for router in self._routers:
			graph += f"\t{router.get_name()} [shape=circle];\n"

		# For each router, create an edge to each destination router
		for router in self._routers:
			for link in router.get_links():
				# Unpack values
				source = link.get_source()
				destination = link.get_destination()

				# Ensure both ends are routers
				if (not isinstance(source.entity, Router) or not isinstance(destination.entity, Router)):
					continue

				# Register the edge in the adjacency matrix
				source_index = get_index(source.entity)
				destination_index = get_index(destination.entity)

				# Cast to RouterNetworkInterface to access cost
				source_interface = cast(RouterNetworkInterface, source.interface)
			
				if (len(adj_matrix[source_index][destination_index]) == 0):
					# Add the edge to the graph
					graph += f'\t{source.entity.get_name()} -- {destination.entity.get_name()} [label="{source_interface.get_cost()}"];\n'
					# Append the edge to the adjacency matrix (undirected graph)
					adj_matrix[source_index][destination_index].append(source_interface.get_cost())
					adj_matrix[destination_index][source_index].append(source_interface.get_cost())
				else:
					# Check if an edge with same cost already exists between the routers
					found_source = source_interface.get_cost() in adj_matrix[source_index][destination_index]
					found_destination = source_interface.get_cost() in adj_matrix[destination_index][source_index]
					
					if not found_source and not found_destination:
						# Append the edge to the graph
						graph += f'\t{source.entity.get_name()} -- {destination.entity.get_name()} [label="{source_interface.get_cost()}"];\n'
						# Save the edge in the adjacency matrix (undirected graph)
						adj_matrix[source_index][destination_index].append(source_interface.get_cost())
						adj_matrix[destination_index][source_index].append(source_interface.get_cost())
					elif not found_source or not found_destination:
						Logger().warning(
							f"Found duplicate link between {source.entity.get_name()} and {destination.entity.get_name()} with same cost. skipping..."
						)

				print(f"Adjacency matrix after adding edge between {source.entity.get_name()} and {destination.entity.get_name()}")
				_print_matrix(adj_matrix)

		graph += "}"
		return graph

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

from typing import cast, Optional
from modules.models.network_elements import Router, RouterNetworkInterface
from dataclasses import dataclass, field

# Priority queue to store the routers to visit
from queue import PriorityQueue

# Source: https://docs.python.org/3/library/queue.html#queue.PriorityQueue
@dataclass(order=True)
class PrioritizedItem:
	priority: float
	item: Router=field(compare=False)

class RouterPathNode:
	def __init__(self, router: Router, via_interface: RouterNetworkInterface, dst_interface: RouterNetworkInterface, cost: float):
		self.router = router
		self.via_interface = via_interface
		self.destination_interface = dst_interface
		self.cost = cost

def compute_routers_shortest_path(routers: list[Router]):
	"""This method explores all the interconnections between routers, computing the shortest path (less cost path) between them.

	Args:
		topology (NetworkTopology): Network topology decoded from the YAML file.
	"""
	
	# Keep track of the distance and previous router for each router
	distance = dict[Router, float]()
	# Reverse graph to backtrack the path
	previous = dict[Router, Optional[RouterPathNode]]() # type: ignore
	# Keep track of used interfaces to avoid using them again
	used_interfaces = dict[Router, list[RouterNetworkInterface]]()

	# Priority queue to store the routers to visit
	Q = PriorityQueue[PrioritizedItem]()
	
	# Copy the routers list to avoid modifying the original list
	routers = routers.copy()
	
	# Select the first router as the starting point
	starting_router = routers[0]
	distance[starting_router] = 0
 
	# Initialize also the distance dictionary 
	for router in routers[1:]:
		distance[router] = float("inf")
		previous[router] = None
		Q.put(PrioritizedItem(distance[router], starting_router))
	  
	# Compute the shortest path between routers using Dijkstra's algorithm (inspired by: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm#Using_a_priority_queue
	while not Q.empty():
		router = Q.get().item
		for link in router.get_links():
			if isinstance(link.endpoint.entity, Router): 
				src_interface = cast(RouterNetworkInterface, link.interface)
				dst_interface = cast(RouterNetworkInterface, link.endpoint.interface)

				# Check if the interface has already been used
				if src_interface in used_interfaces.get(router, []):
					continue
								
				# Get both source and destination interfaces
				src_cost = src_interface.get_cost()
				dst_cost = dst_interface.get_cost()

				# Get the actual cost of the link
				link_cost = max(src_cost, dst_cost)
				
				# Get the distance from the source router to the destination router
				alt = distance[router] + link_cost	
				if alt < distance[link.endpoint.entity]:
					distance[link.endpoint.entity] = alt
					previous[link.endpoint.entity] = RouterPathNode(
						router,
						dst_interface,
						src_interface,
						link_cost
					)
					Q.put(PrioritizedItem(alt, link.endpoint.entity))

					# Mark the interface as used
					if router not in used_interfaces:
						used_interfaces[router] = []
					used_interfaces[router].append(src_interface)
	
	# Return the distance and previous dictionaries
	return distance, previous
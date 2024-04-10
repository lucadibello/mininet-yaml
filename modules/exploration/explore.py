from typing import cast, Optional
from modules.models.network_elements import Router, RouterNetworkInterface
from modules.models.topology import NetworkTopology
from dataclasses import dataclass, field
from typing import Any

# Priority queue to store the routers to visit
from queue import PriorityQueue

# Source: https://docs.python.org/3/library/queue.html#queue.PriorityQueue
@dataclass(order=True)
class PrioritizedItem:
    priority: float
    item: Router=field(compare=False)

class RouterPathNode:
    def __init__(self, router: Router, interface: RouterNetworkInterface, cost: float):
        self.router = router
        self.interface = interface
        self.cost = cost

# Keep track of the distance and previous router for each router
distance = dict[Router, float]()
# Reverse graph to backtrack the path
previous = dict[Router, Optional[RouterPathNode]]() # type: ignore
# Keep track of the visited routers
visited_routers = set()

# Priority queue to store the routers to visit
Q = PriorityQueue[PrioritizedItem]()

def compute_routers_shortest_path(routers: list[Router]):
    """This method explores all the interconnections between routers, computing the shortest path (less cost path) between them.

    Args:
        topology (NetworkTopology): Network topology decoded from the YAML file.
    """
    
    # Initialization: clear from possible previous runs
    visited_routers.clear()
    Q.queue.clear()

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
                src_inte #FIXME: CONTINUE FROM HERE
                # Get both source and destination interfaces
                src_cost = cast(RouterNetworkInterface, link.interface).get_cost()
                dst_cost = cast(RouterNetworkInterface, link.endpoint.interface).get_cost()
                # Get the actual cost of the link
                link_cost = max(src_cost, dst_cost)
                
                # Get the distance from the source router to the destination router
                alt = distance[router] + link_cost	
                if alt < distance[link.endpoint.entity]:
                    distance[link.endpoint.entity] = alt
                    previous[link.endpoint.entity] = RouterPathNode(router, link.interface, link_cost)
                    Q.put(PrioritizedItem(alt, link.endpoint.entity))
    
    # Return the distance and previous dictionaries
    return distance, previous
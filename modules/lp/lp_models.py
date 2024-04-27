from typing import Iterator, Optional, cast
from modules.lp.solver import LpSolver
from modules.models.network_elements import RouterNetworkInterface
from modules.util.logger import Logger
from modules.virtualization.network_elements import Route, VirtualNetworkElement, VirtualRouter

class LPTask():
    """
    This class describes a Linear Programming problem with useful methods to interact with external tools/libraries.
    """
    
    def __init__(self):
        self.objective: Optional[str] = None
        self.is_maximization: Optional[bool] = None
        self.subject_to: dict[str, str] = dict[str, str]()
        self.variables: dict[str, tuple[float, float]] = dict[str, tuple[float, float]]()
    
    def to_cplex(self) -> str:
        """
        This method returns a string with the Linear Programming problem in CPLEX format.
        """
        raise NotImplementedError("Still in development!")

    def set_objective(self, objective: str, is_maximization: bool = True):
        """
        This method allows to set the objective of the Linear Programming problem.
        """
        self.objective = objective
        self.is_maximization = is_maximization
        
    def add_constraint(self, constraint: str, name: str):
        """
        This method allows to add a new constraint to the Linear Programming problem.
        """
        self.subject_to[name] = constraint

    def add_variable(self, name: str, lower_bound: float = 0.0, upper_bound: float = LpSolver.INFINITY):
        """
        This method allows to add a new variable to the Linear Programming problem.
        """
        self.variables[name] = (lower_bound, upper_bound)

class LPNetwork():
    class LPRoute():
        def __init__(self, src: VirtualNetworkElement, route: Route):
            self._src_element = src
            self._route = route
            
            # Check if source is a router interface
            self._lp_variable_name = f"x_{src.get_name()}_{route.to_element.get_name()}_{route.dst_interface.physical_interface.get_name()}"
 
            # If the route is a route between routers, we need also to register the cost of the route
            if isinstance(route.to_element, VirtualRouter):
                # The cost of the route is the cost of the destination interface
                self._cost = cast(RouterNetworkInterface, route.dst_interface.physical_interface).get_cost()
            else:
                # If we are not a router, we need to check if there are some demands specified by the user
                demands = src.get_physical_element().get_demands() 
                
                # Check if we have one or more demands (small optimization to avoid multiple calls to get_demands() method)
                if len(demands) > 0:
                    self._cost = demands[0].maximumTransmissionRate
                elif len(demands) > 1:
                    Logger().warning(f"Element {src.get_name()} has more than one demand specified. Using the strictest demand as the cost of the route.")
                    self._cost = min([demand.maximumTransmissionRate for demand in demands])
                else:
                    # If we are not a router, we have no maximum transmission rate so we have unlimited bandwidth
                    self._cost = LpSolver.INFINITY

        @property
        def src_element(self) -> VirtualNetworkElement:
            return self._src_element
        
        @property
        def dst_element(self) -> VirtualNetworkElement:
            return self._route.to_element

        @property
        def lp_variable_name(self) -> str:
            return self._lp_variable_name
        
        @property
        def route(self) -> Route:
            return self._route
        
        @property
        def cost(self) -> float:
            return self._cost

        def __str__(self):
            return f"LPRoute '{self.lp_variable_name}', cost={self.cost} = {self.src_element.get_name()}:{self.route.via_interface.name} -> {self.dst_element.get_name()}:{self.route.dst_interface.name}"

        def __repr__(self) -> str:
            return self.__str__()

    def __init__(self):
        # Utility dictionaries to lookup routes by variable name or by route
        self._variable_to_route = dict[str, LPNetwork.LPRoute]()
        self._route_to_variable = dict[Route, str]()

        # Global array of routes (useful for debugging / iteration)
        self._routes = list[LPNetwork.LPRoute]()

        # Undirected graph of routes using adjacency list
        self._adjacency_list = dict[VirtualNetworkElement, dict[VirtualNetworkElement, list[LPNetwork.LPRoute]]]()
    
    def add_route(self, lp_route: LPRoute):
        # Reverse the route to add it in the opposite direction
        lp_route_rev = LPNetwork.LPRoute(lp_route.dst_element, lp_route.route.reverse(lp_route.src_element))
        
        # Register both routes in the lookup table(s)
        for lpr in [lp_route, lp_route_rev]:
            # Log both routes
            self._route_to_variable[lpr.route] = lpr.lp_variable_name
            self._variable_to_route[lpr.lp_variable_name] = lpr

            # If source element not present, entire entry is not present
            if lpr.src_element not in self._adjacency_list:
                self._adjacency_list[lpr.src_element] = dict[VirtualNetworkElement, list[LPNetwork.LPRoute]]()
                self._adjacency_list[lpr.src_element][lpr.dst_element] = list[LPNetwork.LPRoute]()
            # If source element present but destination element not present, we need only to create the list for the destination element
            elif lpr.dst_element not in self._adjacency_list[lpr.src_element]:
                self._adjacency_list[lpr.src_element][lpr.dst_element] = list[LPNetwork.LPRoute]()
        
            # Add route in the given direction
            self._adjacency_list[lpr.src_element][lpr.dst_element].append(lpr)
            self._routes.append(lpr)

    def traverse_network_bfs(self, start_element: Optional[VirtualNetworkElement] = None) -> Iterator[tuple[VirtualNetworkElement, LPRoute]]:
        """
        This method allows to traverse the entire network using a Breadth-First Search algorithm, yielding each new element along with the LPRoute object that represents the connection
        between the current element and the previous element.
        """
        visited = set[VirtualNetworkElement]()
        queue = list[VirtualNetworkElement]()

        # If the adjacency list is empty, we have no routes to traverse so we can simply return an empty list
        if len(self._adjacency_list) == 0:
            return list[tuple[VirtualNetworkElement, LPNetwork.LPRoute]]()
        
        # Append to the queue a random element (in this case, the first element of the adjacency list)
        if start_element is not None:
            queue.append(start_element)
        else: 
            queue.append(list(self._adjacency_list.keys())[0])
        
        # Start from the first element
        while len(queue) > 0:
            # Get the current element
            current = queue.pop(0)

            # If the current element is not visited, we need to visit it
            if current not in visited:
                # Mark the element as visited
                visited.add(current)
                
                # Yield the current element and the LPRoute object
                for dst_element, routes in self._adjacency_list[current].items():
                    for route in routes:
                        # Continue exploring only if we have found an unvisited element
                        if dst_element not in visited:
                            yield (dst_element, route)
                            queue.append(dst_element)

    def get_lproute_from_variable(self, variable: str) -> LPRoute:
        return self._variable_to_route[variable]

    def get_variable_name_from_route(self, route: Route) -> str:
        return self._route_to_variable[route]

    def has_route(self, route: Route) -> bool:
        return route in self._route_to_variable

    def get_lp_routes(self) -> list[LPRoute]:
        return self._routes
 
    def get_adjacency_lookup_table(self) -> dict[VirtualNetworkElement, dict[VirtualNetworkElement, list[LPRoute]]]:
        return self._adjacency_list

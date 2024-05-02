from typing import Optional, cast
from modules.lp.solver import LpSolver
from modules.models.network_elements import Demand, RouterNetworkInterface
from modules.util.logger import Logger
from modules.virtualization.network_elements import Route, VirtualNetworkElement, VirtualNetworkInterface, VirtualRouter

class LPTask():
    """
    This class describes a Linear Programming problem with useful methods to interact with external tools/libraries.
    """

    class LPConstraintGroup():
        def __init__(self, comment: str):
            self._constraints = dict[str, str]()
            self._comment = comment
        
        def add_constraint(self, name: str, constraint: str):
            self._constraints[name] = constraint
        
        def get_constraints(self) -> dict[str, str]:
            return self._constraints
        
        def get_comment(self) -> str:
            return self._comment
        

    def __init__(self):
        self.objective: Optional[str] = None
        self.is_maximization: Optional[bool] = None
        self.subject_to: dict[str, str] = {}
        self.variables: dict[str, tuple[float, float]] = {}
        self.binary_variables: set[str] = set()
        self.constraint_groups: list[LPTask.LPConstraintGroup] = []
    
    def to_cplex(self) -> str:
        """
        This method returns a string with the Linear Programming problem in CPLEX format.
        """
        obj_type = "Maximize" if self.is_maximization else "Minimize"
        cplex = ""
        cplex += f"{obj_type}\n"
        cplex += f"\tobj: {self.objective}\n"
        cplex += "\n"
        cplex += "Subject To\n"
        
        # Print all constraint blocks
        for group in self.constraint_groups:
            if len(group.get_comment()) > 0:
                cplex += f"\t\\ {group.get_comment()}\n"
            for name, constraint in group.get_constraints().items():
                cplex += f"\t{name}: {constraint}\n"
            cplex += "\n"
        # Print all single constraints
        for name, constraint in self.subject_to.items():
            cplex += f"\t{name}: {constraint}\n"
        cplex += "\n"

        # Print all integer variables 
        if len(self.variables):
            cplex += "Bounds\n"
            for name, bounds in self.variables.items():
                # If one of the bounds is infinity, we need to handle it differently
                if abs(bounds[0]) == LpSolver.INFINITY:
                    cplex += f"\t{name} >= {bounds[1]}\n"
                elif abs(bounds[1]) == LpSolver.INFINITY:
                    cplex += f"\t{name} <= {bounds[0]}\n"
                else:
                    cplex += f"\t{bounds[0]} <= {name} <= {bounds[1]}\n"

        # Add binary variables
        if len(self.binary_variables):
            cplex += "Binary\n"
            for name in self.binary_variables:
                cplex += f"\t{name}\n"
    
            cplex += "End"
        
        # Return cplex problem as string
        return cplex        

    def set_objective(self, objective: str, is_maximization: bool = True):
        """
        This method allows to set the objective of the Linear Programming problem.
        """
        self.objective = objective
        self.is_maximization = is_maximization
        
    def add_constraint(self, name: str, constraint: str):
        """
        This method allows to add a new constraint to the Linear Programming problem.
        """
        self.subject_to[name] = constraint
 
    def add_constraint_group(self, group: LPConstraintGroup):
        """
        This method allows to add a new group of constraints with an optional comment to the Linear Programming problem.
        """
        self.constraint_groups.append(group)

    def add_binary_variable(self, name: str):
        """
        This method allows to add a new binary variable to the Linear Programming problem.
        """
        if name in self.variables:
            raise ValueError("Variable already present in the LP problem")
        self.binary_variables.add(name)
 
    def add_variable(self, name: str, lower_bound: float = 0.0, upper_bound: float = LpSolver.INFINITY):
        """
        This method allows to add a new variable to the Linear Programming problem.
        """
        if lower_bound > upper_bound:
            raise ValueError("Lower bound is greater than lower bound")
        self.variables[name] = (lower_bound, upper_bound)
    
    def set_flows(self, flows: dict[Demand, str]):
        self.flows = flows
        
    def get_flows(self) -> dict[Demand, str]:
        return self.flows

class LPNetwork():
    class LPRoute():
        def __init__(self, src: VirtualNetworkElement, route: Route, prefix: str = ""):
            self._src_element = src
            self._route = route
            
            # Check if source is a router interface
            self._lp_variable_name = f"{prefix+'_' if len(prefix) > 0 else ''}{src.get_name()}_{route.to_element.get_name()}_{route.dst_interface.physical_interface.get_name()}"
 
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
        self._routes = set[LPNetwork.LPRoute]()

        # Undirected graph of routes using adjacency list
        self._adjacency_list = dict[VirtualNetworkElement, dict[VirtualNetworkElement, list[LPNetwork.LPRoute]]]()

        # Keep track of reverse routes
        self._reverse_routes = dict[Route, LPNetwork.LPRoute]()

    def add_route(self, lp_route: LPRoute):
        # Reverse the route to add it in the opposite direction
        lp_route_rev = LPNetwork.LPRoute(lp_route.dst_element, lp_route.route.reverse(lp_route.src_element))

        # Save reverse route with the same cost as the original route
        self._reverse_routes[lp_route.route] = lp_route_rev
        self._reverse_routes[lp_route_rev.route] = lp_route

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
            
            # Append only routes that are local to the source element
            self._routes.add(lpr)
    
    def find_paths(self, src: VirtualNetworkElement, dst: VirtualNetworkElement) -> list[list[tuple[VirtualNetworkElement, LPRoute]]]:
        # Validate input
        if src not in self._adjacency_list:
            raise ValueError(f"Origin element not found in the adjacency list")
        if dst not in self._adjacency_list:
            raise ValueError(f"Destination element not found in the adjacency list")

        # Initialize the data structure to find paths
        found_paths = []
        stack = [(src, [])]

        while stack:
            current, path = stack.pop()

            # If we have reached the destination, register the path
            if current == dst:
                found_paths.append(path)
                continue
            
            # Explore neighbors
            for neighbor, routes_to_neighbor in self._adjacency_list[current].items():
                for route in routes_to_neighbor:
                    entry = (neighbor, route)
                    rev_entry = (current, self._reverse_routes[route.route])
                    # Check if the neighbor has already been visited in the current path
                    if all(entry != p and rev_entry != p for p in path):  # Check that this node has not been visited in the current path
                        new_path = path + [entry]
                        stack.append((neighbor, new_path))
                        print(f"Adding {neighbor.get_name()} via {route} to the stack")

        # Return all the paths
        return found_paths

    def get_lproute_from_variable(self, variable: str) -> LPRoute:
        return self._variable_to_route[variable]

    def get_variable_name_from_route(self, route: Route) -> str:
        return self._route_to_variable[route]

    def get_reverse_lp_route(self, route: Route) -> LPRoute:
        return self._reverse_routes[route]

    def get_lp_routes(self) -> set[LPRoute]:
        return self._routes
 
    def get_adjacency_lookup_table(self) -> dict[VirtualNetworkElement, dict[VirtualNetworkElement, list[LPRoute]]]:
        return self._adjacency_list
    
    def has_route(self, route: Route) -> bool:
        return route in self._route_to_variable
  
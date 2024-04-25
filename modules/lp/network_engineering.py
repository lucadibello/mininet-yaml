from typing import cast
from modules.lp.task import LPTask
from modules.models.network_elements import Router, RouterNetworkInterface
from modules.virtualization.network_elements import Route, VirtualNetwork, VirtualNetworkElement, VirtualRouter

class LPNetwork():
    class LPRoute():
        def __init__(self, src: VirtualNetworkElement, route: Route):
            self._src_element = src
            self._route = route
            self._lp_variable_name = f"x_{src.get_name()}_{route.to_element.get_name()}_{route.dst_interface.physical_interface.get_name()}"

            # If the route is a route between routers, we need also to register the cost of the route
            if isinstance(route.to_element, VirtualRouter):
                # The cost of the route is the cost of the destination interface
                self._cost = cast(RouterNetworkInterface, route.dst_interface.physical_interface).get_cost()
            else:
                # The cost of the route is zero (we do not have a minimum Mbps requirement for hosts)
                self._cost = 0

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
        self._variable_to_route = dict[str, LPNetwork.LPRoute]()
        self._route_to_variable = dict[Route, str]()
        self._routes = list[LPNetwork.LPRoute]()
    
    def add_route(self, lp_route: LPRoute):
        self._routes.append(lp_route)
        # Register route in lookup table
        self._route_to_variable[lp_route.route] = lp_route.lp_variable_name
        self._variable_to_route[lp_route.lp_variable_name] = lp_route
    
    def get_lproute_from_variable(self, variable: str) -> "LPRoute":
        return self._variable_to_route[variable]

    def get_variable_name_from_route(self, route: Route) -> str:
        return self._route_to_variable[route]

    def has_route(self, route: Route) -> bool:
        return route in self._route_to_variable
    
    def get_lp_routes(self) -> list[LPRoute]:
        return self._routes
 

from typing import cast
from modules.lp.task import LPTask
from modules.models.network_elements import Router, RouterNetworkInterface
from modules.virtualization.network_elements import Route, VirtualNetwork


def lp_task_from_virtual_network(virtual_network: VirtualNetwork) -> LPTask:
    """
    This function takes a VirtualNetwork object and returns a Linear Programming task object that represents the network
    engineering problem of the virtual network. The Linear Programming task should be ready to be solved by an external
    tool/library.
    """
    
    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    
    # 1) Each unique route in the virtual network should be represented as a variable in the Linear Programming problem.
    route_to_variable = dict[Route, str]()
    route_to_cost = dict[Route, float]()
    for router in virtual_network.get_routers():
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in router.get_routes():
            if route not in route_to_variable:
                # Ensure that the route is between two different routers as we are interested in the cost of the route
                if not isinstance(route.to_element, Router):
                    continue

                # Name formatted as "x_<start>_<end>_<end_intf>"
                route_to_variable[route] = f"x_{router.get_name()}_{route.to_element.get_name()}_{route.dst_interface.name}"
                # Now, save also the cost of this route in the dictionary (the cost is the cost of the src interface!)
                route_to_cost[route] = cast(RouterNetworkInterface, route.dst_interface).get_cost()

    # 2) The objective function should maximize the minimum utilization of the network interfaces.
    objective_function = "maximize: "

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
    # return LPTask()
from modules.lp.lp_models import LPNetwork, LPTask
from modules.virtualization.network_elements import VirtualNetwork

def traffic_engineering_task_from_virtual_network(virtual_network: VirtualNetwork) -> LPTask:
    """
    This function takes a VirtualNetwork object and returns a Linear Programming task object that represents the traffic
    engineering problem of the virtual network. The Linear Programming task should be ready to be solved by an external
    tool/library.
    """
    
    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    lp_network = LPNetwork()
    
    # 1) Each unique route in the virtual network should be represented as a variable in the Linear Programming problem.
    for router in virtual_network.get_routers():
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in router.get_routes():
            # Register the route in the LP network if not present
            if not lp_network.has_route(route):
                lp_network.add_route(LPNetwork.LPRoute(router, route))

    # 2) Traverse the virtual network node by node and add the constraints to the Linear Programming problem.
    for element, lp_route in lp_network.traverse_network_bfs():
        # For each element, add the constraints to the Linear Programming problem
        pass

    # 2) The objective function should maximize the minimum utilization of the network interfaces.
    objective_function = "maximize: "
    

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
    # return LPTask()
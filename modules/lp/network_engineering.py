from modules.lp.lp_models import LPNetwork, LPTask
from modules.virtualization.network_elements import VirtualNetwork

def neteng_lp_task_from_virtual_network(virtual_network: VirtualNetwork) -> LPTask:
    """
    This function takes a VirtualNetwork object and returns a Linear Programming task object that represents the network
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

    # For each route, print the cost
    for lp_route in lp_network.get_lp_routes():
        print(lp_route)

    # 2) The objective function should maximize the minimum utilization of the network interfaces.
    objective_function = "maximize: "
    

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
    # return LPTask()
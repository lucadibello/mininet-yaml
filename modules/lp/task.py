from modules.lp.network_engineering import LPNetwork
from modules.virtualization.network_elements import VirtualNetwork

class LPTask():
    """
    This class describes a Linear Programming problem with useful methods to interact with external tools/libraries.
    """
    
    def __init__(self, objective: str, is_maximization: bool = True, subject_to: list = [], variables: dict[str, float] = {}) -> None:
        self.objective = objective
        self.is_maximization = is_maximization
        self.subject_to = subject_to
        self.variables = variables
    
    def to_cplex(self) -> str:
        """
        This method returns a string with the Linear Programming problem in CPLEX format.
        """

        raise NotImplementedError("Still in development!")

def lp_task_from_virtual_network(virtual_network: VirtualNetwork) -> LPTask:
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
        print("Scanning router", router.get_name(), "total routes:", len(router.get_routes()))
        for route in router.get_routes():
            # Register the route in the LP network if not present
            if not lp_network.has_route(route):
                lp_network.add_route(LPNetwork.LPRoute(router, route))

    # For each route, print the cost
    print("Routes and their costs:")
    for lp_route in lp_network.get_lp_routes():
        print(lp_route)

    # 2) The objective function should maximize the minimum utilization of the network interfaces.
    objective_function = "maximize: "
    

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
    # return LPTask()
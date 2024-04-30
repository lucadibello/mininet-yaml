from typing import cast

from modules.lp.lp_models import LPNetwork, LPTask
from modules.lp.solver import GLOPSolver, LpSolver
from modules.models.network_elements import NetworkElement
from modules.models.topology import NetworkTopology
from modules.util.logger import Logger
from modules.virtualization.network_elements import Route, VirtualHost, VirtualNetwork, VirtualNetworkElement, VirtualRouter, VirtualSwitch

from ortools.linear_solver.pywraplp import Objective, Variable

def traffic_engineering_task_from_virtual_network(topology: NetworkTopology, virtual_network: VirtualNetwork) -> LPTask:
    """
    This function takes a VirtualNetwork object and returns a Linear Programming task object that represents the traffic
    engineering problem of the virtual network. The Linear Programming task should be ready to be solved by an external
    tool/library.
    """
    
    def get_virt(src: NetworkElement):
        virt_src = virtual_network.get(src.get_name())
        if virt_src is None:
            raise ValueError(f"Virtual element {src.get_name()} not found in the virtual network.")
        return virt_src
    
    total_constraints = 0
    def next_alpha_id():
        nonlocal total_constraints
        
        # Check if we need multiple letters
        str_id = ""
        if total_constraints // 26 == 0:
            str_id =  chr(65 + total_constraints)
        else:
            remaining = total_constraints
            while(remaining > 0):
                str_id += chr(65 + (remaining % 26))
                remaining = remaining // 26

        # Return string
        total_constraints += 1
        return str_id

    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    lp_network = LPNetwork()
    task = LPTask()

    # 1) Each unique route in the virtual network should be represented as a variable in the Linear Programming problem.
    for element in virtual_network.get_routers() + virtual_network.get_switches():
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in element.get_routes():
            # Print added route
            if route.is_registered and not lp_network.has_route(route):
                # Register the route in the LP network if not present
                lp_network.add_route(LPNetwork.LPRoute(element, route))

    # 2) Load LP solver 
    glop = GLOPSolver()

    # 3) Create lookup table to match the variable name with the OR-Tools variable
    variable_lookup = dict[str, Variable]()
    
    # 4) Define all the variables of the LP problem
    for lp_route in lp_network.get_lp_routes():
        # We skip the routes that connect hosts
        if lp_route.cost > 0:
            # create variable in lp model
            variable_lookup[lp_route.lp_variable_name] = glop.solver.NumVar(0, lp_route.cost, lp_route.lp_variable_name)
            # register variable in lptask
            print(f"added variable: 0 <= {lp_route.lp_variable_name} <= {lp_route.cost}")
            task.add_variable(lp_route.lp_variable_name, 0, lp_route.cost)
        else:
            # Create variable in LP model
            variable_lookup[lp_route.lp_variable_name] = glop.solver.NumVar(lp_route.cost, 0, lp_route.lp_variable_name)
            # Register variable in LPTask
            print(f"Added variable: {lp_route.cost} <= {lp_route.lp_variable_name} <= 0")
            task.add_variable(lp_route.lp_variable_name, lp_route.cost, 0)

    # 5) Define objective function: maximize the minimum effectiveness ratio of all the demands
    variable_lookup["min_r"] = glop.solver.NumVar(0, 1, "min_r")
    objective = cast(Objective, glop.solver.Objective())
    objective.SetCoefficient(variable_lookup["min_r"], 1)
    objective.SetMaximization()
    task.set_objective("min_r", is_maximization=True)

    # Set the maximum transmission rate of both the source interface 
    for demand in topology.get_demands(): 
        src = demand.source

        # Create variable for the lambda variable (in-flow of a particular demand)
        demand_variable = glop.solver.NumVar(0, demand.maximumTransmissionRate, f"dem_{src.get_name()}")
        variable_lookup[f"dem_{src.get_name()}"] = demand_variable
        task.add_variable(f"dem_{src.get_name()}", 0, demand.maximumTransmissionRate)
        
        # We add also the constraint for the maximization of the minimum effectiveness ratio
        glop.solver.Add(variable_lookup["min_r"] - demand_variable <= 0)
        task.add_constraint(f"r_{next_alpha_id()}", f"min_r - dem_{src.get_name()} <= 0")
    
    # Find all the possible routes from the source to the destination in the virtual network
    for demand in topology.get_demands():
        # Get the source and destination virtual elements
        source = get_virt(demand.source)
        destination = get_virt(demand.destination)

        # Find all possible routes between the two elements
        src_to_dst_routes = lp_network.find_paths(source, destination)

        if len(src_to_dst_routes) == 0:
            Logger().warning(f"No route found between {source.get_name()} and {destination.get_name()}")
            continue

        # Print all the routes
        for path in src_to_dst_routes:
            for node in path:
                print(node.get_name(), end=" -> ")
            print("")
    # Print in CPLEX format
    print(task.to_cplex())
     
    # 98) Run solver and create LPResult
    Logger().info("Solving the Traffic Engineering Linear Programming problem...")
    result = glop.solve()
    Logger().info(f"Done. Result: {result.status}, {result.objective_value}, {result.variables}")

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
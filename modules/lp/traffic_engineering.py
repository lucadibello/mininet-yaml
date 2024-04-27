from typing import cast

from modules.lp.lp_models import LPNetwork, LPTask
from modules.lp.solver import GLOPSolver
from modules.models.network_elements import NetworkElement
from modules.models.topology import NetworkTopology
from modules.util.logger import Logger
from modules.virtualization.network_elements import VirtualNetwork

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
                print(remaining, str_id)
                remaining = remaining // 26

        # Return string
        total_constraints += 1
        return str_id

    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    lp_network = LPNetwork()
    task = LPTask()

    # 1) Each unique route in the virtual network should be represented as a variable in the Linear Programming problem.
    for element in virtual_network.get_routers() + virtual_network.get_hosts() + virtual_network.get_switches():
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in element.get_routes():
            # Print added route
            print("Adding route from ", element.get_name(), " to ", route.to_element.get_name(), " via ", route.dst_interface.physical_interface.get_name())
            if not lp_network.has_route(route):
                # Register the route in the LP network if not present
                lp_network.add_route(LPNetwork.LPRoute(element, route))
                print("\t OK")

    # 2) Load LP solver 
    glop = GLOPSolver()

    # 3) Create lookup table to match the variable name with the OR-Tools variable
    variable_lookup = dict[str, Variable]()
    
    # 4) Define all the variables of the LP problem
    for lp_route in lp_network.get_lp_routes():
        # Create variable in LP model
        variable_lookup[lp_route.lp_variable_name] = glop.solver.NumVar(0, lp_route.cost, lp_route.lp_variable_name)
        # Register variable in LPTask
        print(f"Added variable: 0 <= {lp_route.lp_variable_name} <= {lp_route.cost}")
        task.add_variable(lp_route.lp_variable_name, 0, lp_route.cost)

    # 5) Define objective function: maximize the minimum effectiveness ratio of all the demands
    variable_lookup["min_r"] = glop.solver.NumVar(0, 1, "min_r")
    objective = cast(Objective, glop.solver.Objective())
    objective.SetCoefficient(variable_lookup["min_r"], 1)
    objective.SetMaximization()

    # 6) Define the min_r variable using constraints
    demands_per_node = [(demand.source,demand.source.get_demands()) for demand in topology.get_demands()]
    for src, demands in demands_per_node:
        # Get the virtual element
        virt_element = get_virt(src)

        # Among the demands of the element, we select the strictest one
        strictest_demand = min(demands, key=lambda d: d.maximumTransmissionRate)
        
        # We know that an element cannot push more than its maximum transmission rate
        constraint_id = next_alpha_id()
        constraint = glop.solver.Constraint(0, strictest_demand.maximumTransmissionRate, constraint_id)

        # For each route connected to src, we must add an entry to the constraint: their sum must be less than the maximum transmission rate!
        constraint_str = ""
        for idx,route in enumerate(virt_element.get_routes()):
            # Get LP route name + ensure that a variable exists for that route
            route_name = lp_network.get_variable_name_from_route(route)
            assert route_name is not None and route_name in variable_lookup

            # Assign the variable to the constraint
            constraint.SetCoefficient(variable_lookup[route_name], 1)

            # Add the variable to the constraint string
            constraint_str += f" + {variable_lookup[route_name].name()}" if idx > 0 else f"{variable_lookup[route_name].name()}"
        constraint_str += f" <= {strictest_demand.maximumTransmissionRate}"
 
        # Add string constraint to the task
        task.add_constraint(constraint_id, constraint_str)

        # Add the constraint ot the objective function
        print("Added new constraint: ", constraint_str)
     
    # 98) Run solver and create LPResult
    Logger().info("Solving the Traffic Engineering Linear Programming problem...")
    result = glop.solve()
    Logger().info(f"Done. Result: {result.status}, {result.objective_value}, {result.variables}")

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
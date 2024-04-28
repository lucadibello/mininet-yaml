from typing import cast

from modules.lp.lp_models import LPNetwork, LPTask
from modules.lp.solver import GLOPSolver, LpSolver
from modules.models.network_elements import NetworkElement
from modules.models.topology import NetworkTopology
from modules.util.logger import Logger
from modules.virtualization.network_elements import Route, VirtualNetwork, VirtualNetworkElement, VirtualRouter, VirtualSwitch

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

    def is_path_valid(route: Route) -> bool:
        return isinstance(route.to_element, VirtualRouter) or isinstance(route.to_element, VirtualSwitch) and route.is_registered


    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    lp_network = LPNetwork()
    task = LPTask()

    # 1) Each unique route in the virtual network should be represented as a variable in the Linear Programming problem.
    for element in virtual_network.get_routers() + virtual_network.get_switches():
        print("Scanning element: ", element.get_name())
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in element.get_routes():
            # Print added route
            print("Adding route: ", route)
            if route.is_registered:
                # Register the route in the LP network if not present
                lp_network.add_route(LPNetwork.LPRoute(element, route))
                print("\t OK")
        print("-----")

    # 2) Load LP solver 
    glop = GLOPSolver()

    # 3) Create lookup table to match the variable name with the OR-Tools variable
    variable_lookup = dict[str, Variable]()
    
    # 4) Define all the variables of the LP problem
    for lp_route in lp_network.get_lp_routes():
        if lp_route.cost > 0:
            # Create variable in LP model
            variable_lookup[lp_route.lp_variable_name] = glop.solver.NumVar(0, lp_route.cost, lp_route.lp_variable_name)
            # Register variable in LPTask
            print(f"Added variable: 0 <= {lp_route.lp_variable_name} <= {lp_route.cost}")
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

    # 6) Define the min_r variable using constraints
    print("setting up min/max problem...")
    demands_per_node = [(demand.source,demand.source.get_demands()) for demand in topology.get_demands()]
    for src, _ in demands_per_node:
        # Get the virtual element
        virt_element = get_virt(src)

        # We know that an element cannot push more than its maximum transmission rate
        minimization_constraint_id = f"min_{next_alpha_id()}"
        constraint = glop.solver.Constraint(-LpSolver.INFINITY, 0, minimization_constraint_id)
        constraint.SetCoefficient(variable_lookup["min_r"], 1)

        # For each route connected to src, we must add an entry to the constraint: their sum must be less than the maximum transmission rate!
        constraint_str = "min_r - "
        found = False
        for idx, route in enumerate(virt_element.get_routes()):
            if not is_path_valid(route):
                continue
            
            # Get LP route name + ensure that a variable exists for that route
            route_name = lp_network.get_variable_name_from_route(route)
            print("Route name: ", route)
            assert route_name is not None and route_name in variable_lookup

            # Assign the variable to the constraint
            constraint.SetCoefficient(variable_lookup[route_name], -1)

            # Add the variable to the constraint string
            constraint_str += f" - {variable_lookup[route_name].name()}" if idx > 0 else f"{variable_lookup[route_name].name()}"

            if not found:
                found = True
        
        # If we have found at least one route, we must add the constraint to the task
        if found:
            constraint_str += f" <= 0"
            # Add string constraint to the task
            task.add_constraint(minimization_constraint_id, constraint_str)
            # Add the constraint ot the objective function
            print("* added new constraint for r_min: ", constraint_str)
        else:
            # Reset the counter
            total_constraints -= 1

    # Now, explore the network and build the flow constraints between the routers
    print("Setting up other constraints for each flow demand...")
    total_constraints = 0
    
    # Explore the graph starting from SRC, and traverse all the routes while creating the constraints
    queue = []
    previous = dict[VirtualNetworkElement, list[tuple[VirtualNetworkElement, list[LPNetwork.LPRoute]]]]()
    visited = set()
    out_routes = dict[VirtualNetworkElement, list[LPNetwork.LPRoute]]()

    # Starting from each demand, we need to build the constraints for the flow
    for src, demands in demands_per_node:
        print(f"Exploring network starting from demand of {src.get_name()}...")
        
        # Get the virtual element
        virt_element = get_virt(src)

        # If we have multiple demands, we select the strictest one
        strictest_demand = min(demands, key=lambda x: x.maximumTransmissionRate)

        # Add the entry of the default element
        if virt_element not in visited:
            visited.add(virt_element)
            previous[virt_element] = []
 
        # Explore the graph!
        while len(queue) > 0:
            # Get the current element
            current_element = queue.pop(0)
            
            print(f"Exploring neighborhood of element {current_element.get_name()} letting a max flow of {strictest_demand.maximumTransmissionRate}")

            # Create the constraint
            constraint_id = next_alpha_id()
            constraint = glop.solver.Constraint(0, 0, constraint_id)

            # Now, explore the whole neighborhood of the current element and generate the constraints: total input = total output
            src_neighborhood = lp_network.get_adjacency_lookup_table()[current_element]
            for dst, routes_to_dst in src_neighborhood.items():
                # If the dst is not visited, we must add it to the queue
                if dst not in visited:
                    queue.append(dst)
                    visited.add(dst)
                    
                    # Assert that dst is has no previous entry
                    assert dst not in previous
                    
                    # Create the entry in the previous dictionary
                    previous[dst] = [] 

                # Save the previous element
                previous[dst].append((current_element, routes_to_dst)) 

                # Register all the routes that are going out of the current element
                if current_element not in out_routes:
                    out_routes[current_element] = []
                out_routes[current_element].extend(routes_to_dst) 
    
    # For each element, we must create the constraints
    for src, _ in demands_per_node:
        # Get the virtual element
        virt_elem = get_virt(src)

        # Create variable with the current demand
        var_name = f"dem_{src.get_name()}"
        variable_lookup[var_name] = glop.solver.NumVar(0, strictest_demand.maximumTransmissionRate, f"dem_{src.get_name()}")
        task.add_variable(var_name, 0, strictest_demand.maximumTransmissionRate)

        # The current demand - all the output flows = 0
        constraint_id = f"src_{next_alpha_id()}"
        constraint = glop.solver.Constraint(-LpSolver.INFINITY, 0, constraint_id)

        # Add positive coefficients to the constraint: max flow - all the output flows = 0 (route whole flow)
        constraint.SetCoefficient(variable_lookup[var_name], 1)
        constraint_str = f"{var_name}"
        
        # Cycle through all output routes
        for out_route in virt_elem.get_routes():
            print("Checking route: ", out_route)
            if not is_path_valid(out_route):
                continue
            
            # Get variable name + lp route
            out_route_name = lp_network.get_variable_name_from_route(out_route)
            lp_route = lp_network.get_lproute_from_variable(out_route_name)

            # Assert that lp route exists
            assert lp_route != None

            # Create the coefficient
            constraint.SetCoefficient(variable_lookup[out_route_name], -1) 
            constraint_str += f" - {out_route_name}"

        # Add constraint to the task
        constraint_str += f" >= 0"
        task.add_constraint(constraint_id, constraint_str)

    # Print in CPLEX format
    print(task.to_cplex())
     
    # 98) Run solver and create LPResult
    Logger().info("Solving the Traffic Engineering Linear Programming problem...")
    result = glop.solve()
    Logger().info(f"Done. Result: {result.status}, {result.objective_value}, {result.variables}")

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore
from typing import Optional, cast

from modules.lp.lp_models import LPNetwork, LPTask
from modules.lp.solver import GLOPSolver
from modules.models.network_elements import Demand, NetworkElement
from modules.models.topology import NetworkTopology
from modules.util.logger import Logger
from modules.virtualization.network_elements import VirtualHost, VirtualNetwork, VirtualNetworkElement, VirtualRouter, VirtualSwitch

from ortools.linear_solver.pywraplp import Objective, Variable

def next_alpha_id(count: int, start_letter: str = "A") -> str:
    # Check if we need multiple letters
    str_id = ""
    if count // 26 == 0:
        # Return the letter
        return chr(ord(start_letter) + count)
    else:
        remaining = count
        # Get the integer value of start and end letter
        while remaining > 0:
            str_id += chr(ord(start_letter) + (remaining % 26))
            remaining = remaining // 26
    return str_id

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

    # To create such method, we need to understand the network engineering problem and how to represent it as a Linear
    # Programming problem.
    lp_network = LPNetwork()
    task = LPTask()

    # Compute unique names for each flow
    flows = dict[Demand, str]()
    counter = 0
    for demand in topology.get_demands():
        flows[demand] = next_alpha_id(counter, start_letter="x")
        counter += 1
  
    # Add all routes of the virtual network to the LP network
    for element in virtual_network.get_routers() + virtual_network.get_switches() + virtual_network.get_hosts():
        # For each router, add its routes to the dictionary if they do not exist yet                
        for route in element.get_routes():
            # Print added route
            if route.is_registered and \
                not lp_network.has_route(route): 
                # Register the route in the LP network if not present
                lp_network.add_route(LPNetwork.LPRoute(element, route))

    # Compute the in and out paths of each element to create the constraints
    in_routes, out_routes = compute_in_out_paths(virtual_network, lp_network)

    # Load LP solver
    glop = GLOPSolver()

    # Create all variables needed for the LP problem
    variable_lookup = dict[str, Variable]()
    for flow_name in flows.values():
        for lp_route in lp_network.get_lp_routes():
            var_name = f"{flow_name}_{lp_route.lp_variable_name}"
            # Create variable in LP model + in LP task
            variable_lookup[var_name] = glop.solver.BoolVar(var_name)
            task.add_binary_variable(var_name)
            # Create variable for flow ratio of flow
            variable_lookup[flow_name] = glop.solver.NumVar(0, 1, flow_name)
            task.add_variable(flow_name, lower_bound=0, upper_bound=1)

    # Define constraints to allow the maximization of the minimum effectiveness ratio
    variable_lookup["min_r"] = glop.solver.NumVar(0, 1, "min_r")
    objective = cast(Objective, glop.solver.Objective())
    objective.SetCoefficient(variable_lookup["min_r"], 1)
    objective.SetMaximization()
    task.set_objective("min_r", is_maximization=True)

    # Create the constraint to maximize the minimum effectiveness ratio
    flow_ratio_group = LPTask.LPConstraintGroup("Set min_r as the minimum of all effectiveness ratios")
    for demand, flow_name in flows.items(): 
        # glop.solver.Add(variable_lookup["min_r"] - {variable_lookup[flow_name]} <= 0)
        flow_ratio_group.add_constraint(f"{flow_name}_min", f"min_r - {flow_name} <= 0")
        # Increase counter by one
        counter += 1
    # Add the constraint group to the task
    task.add_constraint_group(flow_ratio_group)

    # Now, add constraints to let solver figure out the ratio of each flow
    group = LPTask.LPConstraintGroup("Define how the ratio is computed for each flow")
    for demand, flow_name in flows.items():
        # Define var names
        ratio_var_name = f"ratio_{flow_name}"
        # The transmission ratio * the cost of the route, must be equal to the maximum transmission rate
        group.add_constraint(f"{flow_name}_flow", f"{demand.maximumTransmissionRate} {flow_name} - {ratio_var_name} = 0")
    task.add_constraint_group(group)

    # For each flow, create the right constraints for flow preservation on each path
    for demand, flow_name in flows.items():
        # Create a constraint group for each flow
        flow_group = LPTask.LPConstraintGroup(f"Define default routes for source and destination of flow {flow_name}")

        # The route connecting the source and the destination of the demand
        # should always be selected by the solver
        src = get_virt(demand.source)
        dst = get_virt(demand.destination)

        # Find all the out routes of src
        src_routes = out_routes[src]
        # Find all the in routes of dst
        dst_routes = in_routes[dst]
        # Now, for each route connected to source and destination
        # set that at most one of them must be selected by the solver

        src_var_names = [flow_name + '_' + route.lp_variable_name for route in src_routes]
        dst_var_names = [flow_name + '_' + route.lp_variable_name for route in dst_routes]
        
        flow_group.add_constraint(f"{flow_name}_src", f"{' + '.join(src_var_names)} = 1")
        flow_group.add_constraint(f"{flow_name}_dst", f"{' + '.join(dst_var_names)} = 1")

        # Register constraint group
        task.add_constraint_group(flow_group)
 
    # For each router and switch, create a constraint
    # Now, we need to create a constraint for mutual exclusion for each flow: only one input route can be chosen
    for flow_name in flows.values():        
        # input_variables = [variable_lookup[route.lp_variable_name] for route in elem_in_routes]
        # glop.solver.Add(sum(input_variables) <= 1) # type: ignore
        in_mutex_group = LPTask.LPConstraintGroup(f"Provide mutual exclusion on INPUT routes on all elements of flow {flow_name}")
        for element in virtual_network.get_routers():
            # Skip if for this element there are no input or output routes
            if len(in_routes[element]) == 0:
                continue
            src_var_names = [flow_name + '_' + route.lp_variable_name for route in in_routes[element]]
            in_mutex_group.add_constraint(f"{flow_name}_in_{element.get_name()}", f"{' + '.join(src_var_names)} <= 1")

        # Now, we need to create another constraint for mutual exclusion: only one output route can be chosen
        # output_variables = [variable_lookup[route.lp_variable_name] for route in elem_out_routes]
        # glop.solver.Add(sum(output_variables) <= 1) # type: ignore
        out_mutex_group = LPTask.LPConstraintGroup(f"Provide mutual exclusion on OUTPUT routes on all elements of flow {flow_name}")
        for element in virtual_network.get_routers():
            # Skip if for this element there are no input or output routes
            if len(out_routes[element]) == 0:
                continue

            # Get all the variable names of the output routes which interconnect routers
            src_var_names = [flow_name + '_' + route.lp_variable_name for route in out_routes[element]]
            out_mutex_group.add_constraint(f"{flow_name}_out_{element.get_name()}", f"{' + '.join(src_var_names)} <= 1")

        # Now, provide mutual exclusion on both INPUT and OUTPUT routes: one node have only one input and one output route
        for element in virtual_network.get_routers():
            # For each element, list all the input and output routes
            elem_in_routes = in_routes[element]
            elem_out_routes = out_routes[element]

            # FIXME: Total input = Total output

        # Add the constraint groups to the task
        task.add_constraint_group(in_mutex_group)
        task.add_constraint_group(out_mutex_group)
 
    # Print in CPLEX format
    print(task.to_cplex())
     
    # 98) Run solver and create LPResult
    Logger().info("Solving the Traffic Engineering Linear Programming problem...")
    result = glop.solve()
    Logger().info(f"Done. Result: {result.status}, {result.objective_value}, {result.variables}")

    # 99) FIXME: Create the Linear Programming task object and return it
    return None # type: ignore

def compute_in_out_paths(virtual_network: VirtualNetwork, lp_network: LPNetwork) -> tuple[dict[VirtualNetworkElement, list[LPNetwork.LPRoute]], dict[VirtualNetworkElement, list[LPNetwork.LPRoute]]]:
    # We build the in_routes and out_routes dictionaries to store the input and output routes of each element
    in_routes: dict[VirtualNetworkElement, list[LPNetwork.LPRoute]] = dict()
    out_routes: dict[VirtualNetworkElement, list[LPNetwork.LPRoute]] = dict()
    for element in virtual_network.get_routers() + virtual_network.get_switches() + virtual_network.get_hosts():
        # Get the adajency matrix of the LP network
        adj = lp_network.get_adjacency_lookup_table()
    
        # Get all output routes of the element
        neighbors = adj[element] 

        # Assert that element is unknown at the moment
        assert element not in in_routes and element not in out_routes

        # From the neighbors, get the routes that actual output routes objects
        out_routes[element] = [lp_route for _, lp_routes in neighbors.items() for lp_route in lp_routes]
        # Figure out the input routes of the element
        in_routes[element] = [lp_route for lp_route in lp_network.get_lp_routes() if lp_route.route.to_element == element]
    
    # Return the in_routes and out_routes dictionaries
    return (in_routes, out_routes)

from typing import Tuple, cast

from modules.lp.lp_models import LPNetwork, LPTask
from modules.lp.solver import GLOPSolver
from modules.models.network_elements import Demand, NetworkElement
from modules.models.topology import NetworkTopology
from modules.virtualization.network_elements import VirtualHost, VirtualNetwork, VirtualNetworkElement, VirtualRouter, VirtualSwitch

from ortools.linear_solver.pywraplp import Objective, Variable

# Prefixes for variable names
MIN_MAX_NAME = "min_r" # Minimum of all computed effectiveness ratios
ROUTE_CAPACITY = "cap"
SRC_OVERALL_FLOW_NAME = "lambda" # The total flow of a specific flow

# Prefixes for constraint names
ELEMENT_MUTEX_IN_ROUTES = "in"
ELEMENT_MUTEX_OUT_ROUTES = "out"
ELEMENT_MUTEX_IN_OUT_ROUTES = "in_out"
ROUTE_CAPACITY_CONSTRAINT = "capacity"

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

def traffic_engineering_task_from_virtual_network(topology: NetworkTopology, virtual_network: VirtualNetwork) -> Tuple[GLOPSolver, LPTask]:
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
			if route.is_registered and not lp_network.has_route(route):
				# Register the route in the LP network if not present
				lp_network.add_route(LPNetwork.LPRoute(element, route))

	# Compute the in and out paths of each element to create the constraints
	in_routes, out_routes = compute_in_out_paths(virtual_network, lp_network)

	def is_valid_route(lp_route: LPNetwork.LPRoute) -> bool:
		return isinstance(lp_route.src_element, VirtualRouter) and isinstance(lp_route.route.to_element, VirtualRouter)

	# Now, get all lp_routes that do not connect to switches or hosts as we know that they don't need
	# to be considered during computation (we limit only router interfaces as we will apply TC rules on them)
	core_lp_routes = [lp_route for lp_route in lp_network.get_lp_routes() if is_valid_route(lp_route)]

	# Load LP solver
	glop = GLOPSolver()

	# Create all variables needed for the LP problem
	variable_lookup = dict[str, Variable]()
	for demand, flow_name in flows.items():
		# Create variable for flow ratio of flow
		variable_lookup[flow_name] = glop.solver.NumVar(0, 1, flow_name)
		task.add_variable(flow_name, lower_bound=0, upper_bound=1)

		# Create variables to keep track of actual flow on each flow
		variable_lookup[SRC_OVERALL_FLOW_NAME + "_" + flow_name] = glop.solver.NumVar(0, demand.maximumTransmissionRate, SRC_OVERALL_FLOW_NAME + "_" + flow_name)
		task.add_variable(SRC_OVERALL_FLOW_NAME + "_" + flow_name, lower_bound=0, upper_bound=demand.maximumTransmissionRate)
		
		for lp_route in core_lp_routes:
			var_name = f"{flow_name}_{lp_route.lp_variable_name}"
			# Create variable in LP model + in LP task
			variable_lookup[var_name] = glop.solver.BoolVar(var_name)
			task.add_binary_variable(var_name)

	# Define constraints to allow the maximization of the minimum effectiveness ratio
	variable_lookup[MIN_MAX_NAME] = glop.solver.NumVar(0, 1, MIN_MAX_NAME)
	objective = cast(Objective, glop.solver.Objective())
	objective.SetCoefficient(variable_lookup[MIN_MAX_NAME], 1)
	for demand in flows.keys():
		objective.SetCoefficient(variable_lookup[flows[demand]], 1)
	objective.SetMaximization()
	# Build the objective function
	total_sum = " + ".join([f"{flow_name}" for flow_name in flows.values()])
	task.set_objective(MIN_MAX_NAME + " + " + total_sum, is_maximization=True)

	# Create the constraint to maximize the minimum effectiveness ratio
	flow_ratio_group = LPTask.LPConstraintGroup("Set min_r as the minimum of all effectiveness ratios")
	for demand, flow_name in flows.items(): 
		# Create constraint for each flow
		constraint_name = f"{flow_name}_min"
		constraint = glop.solver.Constraint(-glop.solver.infinity(), 0, constraint_name)
		constraint.SetCoefficient(variable_lookup[MIN_MAX_NAME], 1)
		constraint.SetCoefficient(variable_lookup[flow_name], -1)
		# Add the constraint to the group
		flow_ratio_group.add_constraint(constraint_name, f"min_r - {flow_name} <= 0")
		# Increase counter by one
		counter += 1
	# Add the constraint group to the task
	task.add_constraint_group(flow_ratio_group)

	# Now, add constraints to let solver figure out the ratio of each flow
	group = LPTask.LPConstraintGroup("Define how the ratio is computed for each flow")
	for demand, flow_name in flows.items():
		# Define var names
		ratio_var_name = f"{SRC_OVERALL_FLOW_NAME}_{flow_name}"
		# Create the constraint
		constraint_name = f"{flow_name}_flow"
		constraint = glop.solver.Constraint(0, 0, constraint_name)
		constraint.SetCoefficient(variable_lookup[flow_name], demand.maximumTransmissionRate)
		constraint.SetCoefficient(variable_lookup[ratio_var_name], -1)
		
		# The transmission ratio * the cost of the route, must be equal to the maximum transmission rate
		group.add_constraint(constraint_name, f"{demand.maximumTransmissionRate} {flow_name} - {ratio_var_name} = 0")
	task.add_constraint_group(group)

	# For each router and switch, create a constraint
	# Now, we need to create a constraint for mutual exclusion for each flow: only one input route can be chosen
	for flow_name in flows.values():        
		in_mutex_group = LPTask.LPConstraintGroup(f"Provide mutual exclusion on INPUT routes on all elements of flow {flow_name}")
		for element in virtual_network.get_routers():
			# Skip if for this element there are no input or output routes
			if len(in_routes[element]) == 0:
				continue

			# Cycle throgh all the input routes and get the variable names
			valid_in_routes = [] 
			src_var_names = []
			constraint_name = f"{flow_name}_{ELEMENT_MUTEX_IN_ROUTES}_{element.get_name()}"
			constraint = glop.solver.Constraint(-glop.solver.infinity(), 1, constraint_name)
			for route in in_routes[element]:
				# skip routes that should not be considered
				if not is_valid_route(route):
					continue
				valid_in_routes.append(route)
				src_var_name = flow_name + '_' + route.lp_variable_name
				src_var_names.append(src_var_name)
				# Build constraint
				constraint.SetCoefficient(variable_lookup[src_var_name], 1)

			in_mutex_group.add_constraint(constraint_name, f"{' + '.join(src_var_names)} <= 1")

		# Now, we need to create another constraint for mutual exclusion: only one output route can be chosen
		out_mutex_group = LPTask.LPConstraintGroup(f"Provide mutual exclusion on OUTPUT routes on all elements of flow {flow_name}")
		for element in virtual_network.get_routers():
			# Skip if for this element there are no input or output routes
			if len(out_routes[element]) == 0:
				continue

			# Get all the variable names of the output routes which interconnect routers
			valid_out_routes = [route for route in out_routes[element] if isinstance(route.dst_element, VirtualRouter)]
			src_var_names = [flow_name + '_' + route.lp_variable_name for route in valid_out_routes]
			
			# Build constraint
			constraint_name = f"{flow_name}_{ELEMENT_MUTEX_OUT_ROUTES}_{element.get_name()}"
			constraint = glop.solver.Constraint(-glop.solver.infinity(), 1, constraint_name)
			for var_name in src_var_names:
				constraint.SetCoefficient(variable_lookup[var_name], 1)
			out_mutex_group.add_constraint(constraint_name, f"{' + '.join(src_var_names)} <= 1")

		# Add the constraint groups to the task
		task.add_constraint_group(in_mutex_group)
		task.add_constraint_group(out_mutex_group)
	
	# Now, provide mutual exclusion on both INPUT and OUTPUT routes: one node have only one input and one output route
	src_dst_routers_per_flow = dict[str, tuple[list[VirtualRouter], list[VirtualRouter]]]()
	# Extract list of sources and list of destinations
	for demand, flow_name in flows.items():
		# Create a list of sources and destinations
		router_src = []
		router_dst = []
		for element in virtual_network.get_routers():
			# Check if current element is:
			# a) connected directly to the source demand
			# b) connected directly to the destination demand
			# c) connected to a switch that is connected to the source demand
			# d) connected to a switch that is connected to the destination demand
			for route in in_routes[element]:
				if route.src_element == get_virt(demand.source):
					router_src.append(element)
				elif route.src_element == get_virt(demand.destination):
					router_dst.append(element)
				elif isinstance(route.src_element, VirtualSwitch):
					# Extract all in-routes of the switch and check if it is connected to the source
					for switch_route in in_routes[route.src_element]:
						if switch_route.src_element == get_virt(demand.source):
							router_src.append(element)
					for switch_route in out_routes[route.src_element]:
						if switch_route.dst_element == get_virt(demand.destination):
							router_dst.append(element)

			# Store the source and destination routers for the flow
			src_dst_routers_per_flow[flow_name] = (router_src, router_dst)
		
	capacity_groups = []
	for demand, flow_name in flows.items():
		# Get the source and destination routers
		router_src, router_dst = src_dst_routers_per_flow[flow_name]
		# Create a constraint group for each flow
		mutex_constraint_group = LPTask.LPConstraintGroup(f"Provide mutual exclusion on INPUT and OUTPUT routes on all elements of flow {flow_name}")
		capacity_constraint_group = LPTask.LPConstraintGroup(f"Define the maximum capacity of each element for flow {flow_name}")
		for element in virtual_network.get_routers():
			# For each element, list all the input and output routes
			valid_in_routes = [route for route in in_routes[element] if isinstance(route.src_element, VirtualRouter)]
			valid_out_routes = [route for route in out_routes[element] if isinstance(route.dst_element, VirtualRouter)]

			# Extract variable names for both groups
			in_var_names = [route.lp_variable_name for route in valid_in_routes]
			out_var_names = [route.lp_variable_name for route in valid_out_routes]
			
			# Compute total			
			if element in router_src:
				total = -1
			elif element in router_dst:
				total = 1
			else:
				total = 0
			
			# Build actual variable names
			in_var_names_binary = [f"{flow_name}_{var_name}" for var_name in in_var_names]
			out_var_names_binary = [f"{flow_name}_{var_name}" for var_name in out_var_names]
			in_var_names_capacity = [f"{flow_name}_{ROUTE_CAPACITY}_{var_name}" for var_name in in_var_names]
			out_var_names_capacity = [f"{flow_name}_{ROUTE_CAPACITY}_{var_name}" for var_name in out_var_names]
			
			# For the mutex constraint:
			# - if element is directly connected to source, we have: 0 input routes, 1 output route (0-1 = -1)
			# - if element is directly connected to destination, we have: 1 input route, 0 output routes (1-0 = 1)
			constraint_name = f"{flow_name}_{ELEMENT_MUTEX_IN_OUT_ROUTES}_{element.get_name()}"
			constraint = glop.solver.Constraint(total, total, constraint_name)
			for in_var_name in in_var_names_binary:
				variable_lookup[in_var_name] = glop.solver.BoolVar(in_var_name)
				constraint.SetCoefficient(variable_lookup[in_var_name], 1)
			for out_var_name in out_var_names_binary:
				variable_lookup[out_var_name] = glop.solver.BoolVar(out_var_name)
				constraint.SetCoefficient(variable_lookup[out_var_name], -1)
			mutex_constraint_group.add_constraint(constraint_name, f"{f' + '.join(in_var_names_binary)} - {f' - '.join(out_var_names_binary)} = {total}")
			
			# For the capacity constraint:
			# - if element is directly connected to source, the overall flow must be equal to the maximum transmission rate of that flow
			# - if element is directly connected to destination, the overall flow must also be equal to the maximum transmission rate of that flow
			# - if element is not connected to source or destination, the overall flow must be equal to 0 as we need to switch its entirety to the next hop
			lambda_var_name = f"{SRC_OVERALL_FLOW_NAME}_{flow_name}" 
			constraint_name = f"{flow_name}_{ROUTE_CAPACITY_CONSTRAINT}_{element.get_name()}"

			# build or-tools constraint
			constraint = glop.solver.Constraint(0, 0, constraint_name)
			for in_var_name in in_var_names_capacity:
				variable_lookup[in_var_name] = glop.solver.IntVar(0, glop.solver.infinity(), in_var_name)
				constraint.SetCoefficient(variable_lookup[in_var_name], 1)
			for out_var_name in out_var_names_capacity:
				variable_lookup[out_var_name] = glop.solver.IntVar(0, glop.solver.infinity(), out_var_name)
				constraint.SetCoefficient(variable_lookup[out_var_name], -1)

			# create constraint in cplex syntax
			base_constraint = f' + '.join(in_var_names_capacity) + " - " + f' - '.join(out_var_names_capacity)
			if element in router_src:
				capacity_constraint_group.add_constraint(constraint_name, base_constraint + f" + {lambda_var_name} = 0")
				constraint.SetCoefficient(variable_lookup[lambda_var_name], 1)
			elif element in router_dst: 
				capacity_constraint_group.add_constraint(constraint_name, base_constraint + f" - {lambda_var_name} = 0")
				constraint.SetCoefficient(variable_lookup[lambda_var_name], -1)
			else:
				capacity_constraint_group.add_constraint(constraint_name, base_constraint + f" = 0")
			
		# Add the constraint group to the task
		task.add_constraint_group(mutex_constraint_group)
		# add the capacity constraint group to the list
		capacity_groups.append(capacity_constraint_group)
	
	# Now, append all capacity constraints to the task
	for group in capacity_groups:
		task.add_constraint_group(group)
 
	# Setup link capacities for each link in all possible flows
	added_routes = set()
	# Create a constraint group for each flow
	flow_group = LPTask.LPConstraintGroup(f"Define overall capacities of each edge in the network for all flows")
	# Keep track of switches connected to the source demand
	core_switches = set()
	for lp_route in core_lp_routes:
		# Check if this route has been added already
		if lp_route in added_routes:
			continue

		# Get the reverse route
		rev_route = lp_network.get_reverse_lp_route(lp_route.route)

		# Add both routes to the set
		added_routes.add(lp_route)
		added_routes.add(rev_route)

		# Generate the names of all variables
		forward_route_var_names = [f"{flow_name}_{ROUTE_CAPACITY}_{lp_route.lp_variable_name}" for flow_name in flows.values()]
		reverse_route_var_names = [f"{flow_name}_{ROUTE_CAPACITY}_{rev_route.lp_variable_name}" for flow_name in flows.values()]

		# If the route connects an element of the demand, the cost should be the maximum transmission rate
		dst_match = src_match = propagation_match = False
		for demand in topology.get_demands():
			for lp_route in [lp_route, rev_route]:
				dst_match = lp_route.route.to_element in [get_virt(demand.destination), get_virt(demand.source)] + list(core_switches)
				src_match = lp_route.src_element in [get_virt(demand.destination), get_virt(demand.source)] + list(core_switches)
				
				# Check if it has been matched
				if not dst_match and not src_match:
					# If the propagation match is true, we need to register the core switches
					propagation_match = any(route.src_element == demand.source for route in in_routes[lp_route.src_element])
					if propagation_match:
						core_switches.add(lp_route.src_element)
	
				if dst_match or src_match or propagation_match:
					break
			if dst_match or src_match or propagation_match:
				break
		override_cost = dst_match or src_match or propagation_match
		
		# Get the right cost of the route
		cost = demand.maximumTransmissionRate if override_cost else lp_route.cost
			
		# Add the constraint to the group
		constraint_name = f"{ROUTE_CAPACITY_CONSTRAINT}_{lp_route.lp_variable_name}"
		constraint = glop.solver.Constraint(-glop.solver.infinity(), cost, constraint_name)
		for var_name in forward_route_var_names + reverse_route_var_names:
			constraint.SetCoefficient(variable_lookup[var_name], 1)
		flow_group.add_constraint(constraint_name, f"{' + '.join(forward_route_var_names + reverse_route_var_names)} <= {cost}")
		
	# Add the constraint to the group
	task.add_constraint_group(flow_group)
	
	# For each binary indicator variable, create a constraint to define the actual flow on the specific route
	for demand, flow_name in flows.items():
		# Create a constraint group for each flow
		flow_group = LPTask.LPConstraintGroup(f"Define the flow on each route of flow {flow_name}")
		for lp_route in core_lp_routes:
			# If the route connects an element of the demand, the cost should be the maximum transmission rate
			dst_match = lp_route.route.to_element in [get_virt(demand.destination), get_virt(demand.source)]
			src_match = lp_route.src_element in [get_virt(demand.destination), get_virt(demand.source)]

			# Get the right cost of the route
			cost = demand.maximumTransmissionRate if dst_match or src_match else lp_route.cost
			
			# Get the variable name of the route
			constraint_name = f"{flow_name}_{ROUTE_CAPACITY_CONSTRAINT}_{lp_route.lp_variable_name}"
			var_name = f"{flow_name}_{ROUTE_CAPACITY}_{lp_route.lp_variable_name}"
			
			# Create constraint in solver + add to task
			constraint = glop.solver.Constraint(-glop.solver.infinity(), 0, constraint_name)
			constraint.SetCoefficient(variable_lookup[var_name], 1)
			constraint.SetCoefficient(variable_lookup[f"{flow_name}_{lp_route.lp_variable_name}"], -cost)
			flow_group.add_constraint(constraint_name, f"{var_name} - {cost} {flow_name}_{lp_route.lp_variable_name} <= 0")

		# Register constraint group
		task.add_constraint_group(flow_group)	

	# Return the generated lp_network and the relative task describing the traffic engineering problem
	return (glop, task)

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

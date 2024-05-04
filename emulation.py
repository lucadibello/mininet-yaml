from modules.args.parser import ArgParser
from modules.lp.solver import LpSolver, SolverStatus
from modules.lp.traffic_engineering import traffic_engineering_task_from_virtual_network, MIN_MAX_NAME, SRC_OVERALL_FLOW_NAME
from modules.yaml.decoder import decodeTopology
from modules.util.logger import Logger
from modules.virtualization.network import create_network_from_virtual_topology

ROUND_DIGITS = 6

def main():
    # Parse + validate arguments
    args = vars(ArgParser().parse())

    # Extract values
    file_path: str = args["definition"]
    must_draw: bool = args["draw"]
    log_dir: str = args["log_dir"]
    is_verbose: bool = args["verbose"]
    is_silent: bool = args["silent"]
    is_lp: bool = args["lp"]
    is_print_goodput: bool = args["print"]

    # Initialize logger singleton with passed settings
    Logger(debug=is_verbose, is_silent=is_silent) if not log_dir else Logger(
        log_dir, debug=is_verbose, is_silent=is_silent
    )

    Logger().debug(f"Reading the network topology from the file: {file_path}")

    # Validate and decode network topology from YAML file
    try:
        topology = decodeTopology(file_path)
        Logger().info(
            f"Network topology loaded. Found {len(topology.get_routers())} routers and {len(topology.get_hosts())} hosts among {len(topology.get_subnets())} subnets. "
            f"Total demands: {len(topology.get_demands())}, "
            f"Total links: { topology.get_total_links()}"
        )

        # Now, handle what the user wants to do with the network topology
        if must_draw:
            Logger().debug("Drawing the network topology...")
            graph = topology.draw()
            Logger().info(
                "Topology graph generated correctly. Output is displayed below."
            )
            # Print the graph to the console
            print(graph)
        else:
            Logger().info("Creating virtual network...")
            has_demands = len(topology.get_demands()) > 0
            # Create and virtualize decoded topology
            easy_mn, virtual_network = create_network_from_virtual_topology(topology)

            # Check if we need to solve the LP problem before starting the network
            if len(topology.get_demands()) > 0:
                # Create the LP problem
                Logger().info("Generating the Traffic Engineering LP problem from the specified demands...")
                glop_solver, traffic_eng_task = traffic_engineering_task_from_virtual_network(topology, virtual_network)
                if is_verbose:
                    glop_solver.set_verbose(True)
                # Check if we need to virtualize or not
                if is_lp:
                    print(traffic_eng_task.get_lp_task().to_cplex())
                else:
                    # Solve the problem + parse it
                    Logger().info("Solving the Traffic Engineering LP problem...")
                    traffic_eng_task.parse_result(glop_solver.solve())

                    # Print all variables
                    if is_verbose:
                        Logger().debug("LP problem variables:")
                        for var in glop_solver.solver.variables():
                            Logger().debug(f"\t * {var.name()} = {var.solution_value()}")  

                    # Check status and warn the user if needed
                    if traffic_eng_task.get_status() == SolverStatus.OPTIMAL or traffic_eng_task.get_status() == SolverStatus.FEASIBLE:
                        # Log the most important information about the result
                        Logger().info(
                            f"LP problem solved with status: {traffic_eng_task.get_status().name}, "
                            f"minimum effectiveness ratio: {round(traffic_eng_task.get_min_effectiveness_ratio(), ROUND_DIGITS)}")
                    elif traffic_eng_task.get_status() == SolverStatus.INFEASIBLE:
                        Logger().warning("LP problem is infeasible, the network will be started without applying any Traffic Engineering rule. "
                                         "All demands will be satisfied with the minimum effectiveness ratio.")
                    else:
                        Logger().fatal(f"LP solver returned an unexpected status value: {traffic_eng_task.get_status().name}.")

                    if is_print_goodput:
                        for idx, flow_data in enumerate(traffic_eng_task.get_flows_data().items()):
                            demand, flow = flow_data
                            demand_str = f"{demand.source.get_name()}->{demand.destination.get_name()} with {demand.maximumTransmissionRate} Mbps"
                            Logger().info(f"Flow #{idx+1} - Demand {demand_str}:")
                            Logger().info(f"\t * optimal effectiveness ratio = {round(flow.effective_ratio, ROUND_DIGITS)} "
                                          f"({round(flow.effective_ratio * 100, 2)}% of the demand is satisfied)")
                            Logger().info(f"\t * actual goodput = {flow.actual_flow} Mbps / {demand.maximumTransmissionRate} Mbps")
                    else:
                        # We need to virtualize the network but also apply the Traffic Control rules
                        try:
                            easy_mn.start_network_with_demands(traffic_eng_task.get_flows_data())
                            easy_mn.start_shell()
                        finally:
                            easy_mn.stop_network()
            else:
                # No LP needed, so we can start right away the virtual network
                try:
                    easy_mn.start_network()
                    easy_mn.start_shell()
                finally:
                    easy_mn.stop_network()
    except ValueError as e:
        Logger().fatal(str(e))

if __name__ == "__main__":
    main()

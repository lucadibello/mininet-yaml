from modules.args.parser import ArgParser
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
            # Create and virtualize decoded topology
            easy_mn, virtual_network = create_network_from_virtual_topology(topology)

            # Check if we need to solve the LP problem before starting the network
            if len(topology.get_demands()) > 0:
                # Create the LP problem
                Logger().info("Generating the Traffic Engineering LP problem from the specified demands...")
                glop_solver, traffic_eng_task = traffic_engineering_task_from_virtual_network(topology, virtual_network)
                glop_solver.set_verbose(True)

                print("Total constraints:", glop_solver.solver.NumConstraints())
                print("Total variables:", glop_solver.solver.NumVariables())
                # Print all variables
                for variable in glop_solver.solver.variables():
                    print(variable.name())

                # Check if we need to virtualize or not
                if is_lp:
                    print(traffic_eng_task.get_lp_task().to_cplex())
                else:
                    # Solve the problem + parse it
                    Logger().info("Solving the Traffic Engineering LP problem...")
                    traffic_eng_task.parse_result(glop_solver.solve())

                    # Log the most important information about the result
                    Logger().info(f"LP problem solved with status: {traffic_eng_task.get_status()}, minimum effectiveness ratio: {traffic_eng_task.get_objective_value}")

                    if is_print_goodput:
                        for demand, flow in traffic_eng_task.get_flows_data().items():
                            demand_str = f"{demand.source.get_name()}->{demand.destination.get_name()} with {demand.maximumTransmissionRate} Mbps"
                            Logger().info(f"Demand {demand_str}:")
                            Logger().info(f"\t * optimal effectiveness ratio is {round(flow.get_effectiveness_ratio(), ROUND_DIGITS)} ({round(flow.get_effectiveness_ratio() * 100, 2)}% of the requested goodput)")
                            Logger().info(f"\t * optimal goodput is {flow.get_actual_flow()} Mbps / {demand.maximumTransmissionRate} Mbps")
                    else:
                        # We need to virtualize the network but also apply the Traffic Control rules
                        try:
                            easy_mn.start_network()
                            # FIXME: easy_mn.apply_traffic_control()
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

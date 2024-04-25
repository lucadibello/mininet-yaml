from modules.args.parser import ArgParser
from modules.lp.network_engineering import lp_task_from_virtual_network
from modules.models.topology import NetworkTopology
from modules.yaml.decoder import decodeTopology
from modules.util.logger import Logger
from modules.virtualization.network import create_network_from_virtual_topology
from mininet.cli import CLI

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
            f"Network topology loaded. Found {len(topology.get_routers())} routers and {len(topology.get_hosts())} hosts among {len(topology.get_subnets())} subnets. Total links: { topology.get_total_links()}"
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
            Logger().debug("Creating virtual network...")
            # Create and virtualize decoded topology
            easy_mn, virtual_network = create_network_from_virtual_topology(topology)

            # If user has requested to print the LP problem or print the goodput, do not virtualize! 
            if is_lp or is_print_goodput:
                Logger().info("Network virtualization skipped. Generating LP problem...")
                lptask = lp_task_from_virtual_network(virtual_network)

                # Print the LP problem in CPLEX format
                if is_lp:
                    Logger().info("LP problem generated. Output is displayed below.")
                    print(lptask.to_cplex())
                else:
                    raise NotImplementedError("Goodput analysis not implemented yet.")
            else:
                # Now, start the virtual network and open the CLI
                try:
                    easy_mn.start_network()
                    easy_mn.start_shell()
                finally:
                    easy_mn.stop_network()
    except ValueError as e:
        Logger().fatal(str(e))


if __name__ == "__main__":
    main()

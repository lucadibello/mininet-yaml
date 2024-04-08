from modules.args.parser import ArgParser
from modules.yaml.decoder import decodeTopology
from modules.util.logger import Logger
from modules.virtualization.network import run_virtual_topology


def main():
    # Parse + validate arguments
    args = vars(ArgParser().parse())

    # Extract values
    file_path: str = args["definition"]
    must_draw: bool = args["draw"]
    log_dir: str = args["log"]
    is_verbose: bool = args["verbose"]
    is_silent: bool = args["silent"]

    # Initialize logger singleton with passed settings
    Logger(debug=is_verbose, is_silent=is_silent) if not log_dir else Logger(
        log_dir, debug=is_verbose)

    Logger().debug(f"Reading the network topology from the file: {file_path}")

    # Validate and decode network topology from YAML file
    try:
        topology = decodeTopology(file_path)
        Logger().info(
            f"Network topology loaded. Found {len(topology.get_routers())} routers and {
                len(topology.get_hosts())} hosts"
            f" among {len(topology.get_subnets())} subnets. Total links: {
                topology.get_total_links()}"
        )

        # Now, handle what the user wants to do with the network topology
        if must_draw:
            Logger().debug("Drawing the network topology...")
            graph = topology.draw()
            Logger().info("Topology graph generated correctly. Output is displayed below.")
            # Print the graph to the console
            print(graph)
        else:
            Logger().debug("Creating virtual network...")
            # Create the virtual network
            run_virtual_topology(topology)

    except ValueError as e:
        Logger().fatal(str(e))


if __name__ == "__main__":
    main()

from modules.args.parser import ArgParser
from modules.util.splashscreen import splashscreen 
from modules.yaml.decoder import decodeTopology
from modules.util.logger import Logger


def main():
	# Parse + validate arguments
	args = vars(ArgParser().parse())

	# Extract values
	file_path: str = args["definition"]
	must_draw: bool = args["draw"]
	log_dir: str = args["log"]
	is_verbose: bool = args["verbose"]

	# Print splash screen
	splashscreen()

	# Initialize logger singleton with passed settings 
	Logger(debug=is_verbose) if not log_dir else Logger(log_dir, debug=is_verbose)

	Logger().info(f"Reading the network topology from the file: {file_path}")

	# Validate and decode network topology from YAML file
	topology = decodeTopology(file_path)
	Logger().info(
		f"Network topology successfully loaded. Found {len(topology.get_routers())} routers, {len(topology.get_hosts())} hosts and {topology.get_total_links()} unique links."
	)

	# Now, handle what the user wants to do with the network topology
	if must_draw:
		Logger().info("Drawing the network topology...")
		graph = topology.draw()
		# Print the graph to the console
		print(graph)
	else:
		Logger().info("Creating virtual network...")
		raise NotImplementedError("The network emulation is not implemented yet.")


if __name__ == "__main__":
	main()

from typing import Optional, TypedDict, cast
from mininet.net import Mininet
from itertools import product

from mininet.node import Node
from mininet.cli import CLI
from modules.lp.traffic_engineering import TrafficEngineeringLPResult
from modules.models.network_elements import Demand, NetworkElement, RouterNetworkInterface
from modules.models.topology import NetworkTopology
from modules.util.exceptions import NetworkError
from modules.util.logger import Logger
from modules.util.mininet import executeChainedCommands, executeCommand
from modules.virtualization.network_elements import Route, VirtualNetwork, VirtualNetworkElement, VirtualNetworkInterface

class TrafficControlSettings(TypedDict):
    burst: tuple[int, str]
    latency: tuple[int, str]
    min_burst: int

_default_settings: TrafficControlSettings = {
    "burst": (5, "kb"),
    "latency": (70, "ms"),
    "min_burst": 1540
}

def ensure_network_started(func):
    """
    Decorator to ensure that the network has been started before calling a method.
    """
    def wrapper(self, *args, **kwargs):
        if not self._is_started:
            raise NetworkError("The virtual network has not been started yet.")
        return func(self, *args, **kwargs)
    return wrapper

class EasyMininet():
    """
    Proxy class to simplify the usage of Mininet in the context of the virtual network representation generated from the YAML network definition.
    """
    
    def __init__(self, net: Mininet, physical_network: NetworkTopology, virtual_network: VirtualNetwork) -> None:
        self._net = net 
        self._physical_network = physical_network
        self._virtual_network = virtual_network
        self._is_started = False

    def start_network_with_demands(self, flows_data: dict[Demand, TrafficEngineeringLPResult.FlowData]):
        
        def _create_marker_rule_commands(marker: int, src_interface: VirtualNetworkInterface, dst_interface: VirtualNetworkInterface) -> list[str]:
            """
            This method creates the command to mark the packets with a specific identifier.
            """
            return [
                f"-t mangle -A PREROUTING -s {src_interface.physical_interface.get_ip()} -d {dst_interface.physical_interface.get_ip()} -j MARK --set-mark {marker}",
                f"-t mangle -A PREROUTING -m mark --mark {marker} -j ACCEPT"
            ]
        
        # Prepare all the IPTable rules for the network
        marker_lookup = dict[Demand, int]()
        for idx, data in enumerate(flows_data.items()):
            # First of all, for each flow we need to create a marker to identify the packets belonging to that flow
            demand, flow_data = data
            
            # Create the marker rule
            maker_id = idx + 1
            marked_routes = dict[int, list[tuple[VirtualNetworkElement, Route]]]()
            marker_lookup[demand] = maker_id
            marked_routes[maker_id] = []

            # Find all virtual interfaces of the source and destination elements
            src_element = self._virtual_network.get(demand.source.get_name())
            dst_element = self._virtual_network.get(demand.destination.get_name())

            assert src_element is not None and dst_element is not None, "Source or destination element not found in the virtual network."

            src_interfaces = src_element.get_virtual_interfaces()
            dst_interfaces = dst_element.get_virtual_interfaces()

            # Get all elements involved in the demands and let them know about the marker
            for path_node in flow_data.flow_path:
                # Get the underlying virtual route
                route = path_node.lp_route.route
                # Get the element + the interface in which we need to apply the traffic control rules to
                target_router = route.to_element

                # Get the Mininet node of the router
                src_node = self._net.get(path_node.lp_route.src_element.get_name())
                dst_node = self._net.get(path_node.lp_route.route.to_element.get_name())
                # Casting
                src_node = cast(Optional[Node], src_node)
                dst_node = cast(Optional[Node], dst_node)
                # Ensure they exist
                if src_node is None or dst_node is None:
                    raise ValueError(
                            f"Node {target_router.get_name()} not found in the virtual network. There is a problem with the network topology."
                    )
                
                # Save the marker for the demand
                marked_routes[maker_id].append((path_node.lp_route.src_element, path_node.lp_route.route))

                # Set a marker for the route
                route.set_marker(maker_id)

                # Execute the iptables commands
                Logger().debug(f"Applying marker rule for demand {demand.source.get_name()} -> {demand.destination.get_name()} on path node {target_router.get_name()}")

                # Get combination of source and destination interfaces
                for src_interface, dst_interface in product(src_interfaces, dst_interfaces):
                    # Create the marker rule for the source and destination interfaces
                    for cmd in _create_marker_rule_commands(maker_id, src_interface, dst_interface):
                        executeCommand(src_node, f"iptables {cmd}")
 
        # We propagate the routes BUT we will mark certain routes with a specific marker
        self._virtual_network.propagate_routes()	
        
        # Start the network normally
        self.start_network(marked_routes) 
        
        # Apply traffic control rules
        self.apply_traffic_control(flows_data, settings=_default_settings)

    def start_network(self, marker_lookup: dict[int, list[tuple[VirtualNetworkElement, Route]]] = dict()):
        """
        This method starts the virtual network and configures the IP addresses and routing tables of all elements of the network
        according to the generated virtual network topology.
        """
        if self._is_started:
            raise NetworkError("The virtual network has already been started.")
        
        # Start Mininet
        Logger().info("Starting the virtual network...")
        self._net.start()

        Logger().debug(
            "Configuring IP addresses of the remaining unconfigured interfaces..."
        )

        # For each network element, configure the IP address of the virtual interfaces
        for element in self._physical_network.get_routers() + self._physical_network.get_hosts():
            # cast element to NetworkElement
            element = cast(NetworkElement, element)

            # Get virtual node
            velement = self._virtual_network.get(element.get_name())
            if velement is None:
                raise ValueError(
                    f"Virtual element {element.get_name()} not found in the virtual network. There is a problem with the network topology."
                )

            # Get virtual mininet node
            node = self._net.get(velement.get_name())
            node = cast(Optional[Node], node)
            if node is None:
                raise ValueError(
                    f"Node {velement.get_name()} not found in the virtual network. There is a problem with the network topology."
                )

            # Get the virtual interfaces already configured
            vintfs = velement.get_virtual_interfaces()
            intfs = element.get_interfaces()

            # Configure the IP address of the missing virtual interfaces
            for intf in intfs:
                if not any(
                    vintf.physical_interface.get_name() == intf.get_name()
                    for vintf in vintfs
                ):
                    intf_name = element.get_name() + "-" + intf.get_name()
                    Logger().warning(
                        f"Interface {intf_name} of element {element.get_name()} is not used in any link. It will be created but kept down to avoid routing problems."
                    )

                    # Create the virtual interface and set the related IP address
                    executeChainedCommands(
                        node,
                        [
                            f"ip link add {intf_name} type veth",
                            f"ifconfig {intf_name} {intf.get_ip()} netmask {intf.get_mask()}",
                            f"ifconfig {intf_name} down",
                        ],
                    )

                    # Register created interface in the virtual network object
                    vintf = VirtualNetworkInterface(
                        name=intf_name, physical_interface=intf)
                    velement.add_virtual_interface(vintf)

        # Add default gateway for each element
        for virt_element in self._virtual_network.get_routers() + self._virtual_network.get_hosts():
            Logger().debug(
                f"Configuring routing table for element {virt_element.get_name()}"
            )
            # Get mininet node
            node = self._net.get(virt_element.get_name())
            # cast to Node type (as Mininet does not specify any return type...)
            node = cast(Optional[Node], node)
            if node is None:
                raise ValueError(
                    f"Element {virt_element.get_name()} not found in the virtual network. There is a problem with the network topology."
                )

            # Define which one is the default gateway for the network element
            gateway = virt_element.get_gateway()
            if gateway:
                Logger().debug("\t * setting shortest path as default gateway...")
                # Now, add default gateway for the element in order to be able to reach subnets outside the ones it is directly connected to
                executeCommand(node, f"ip route add default via {gateway.ip}")
            else:
                Logger().debug(
                    f"\t [!] element {virt_element.get_name()} does not have a default gateway defined."
                )
            
            # Group routes by destination subnet
            routes = dict[str, list[Route]]()
            for route in virt_element.get_routes():
                # Skip registered routes
                if route.is_registered:
                    continue
                # Build network IP
                ip_with_prefix = f"{route.subnet.network_address()}/{route.subnet.get_prefix_length()}"
                if ip_with_prefix not in routes:
                    routes[ip_with_prefix] = []
                routes[ip_with_prefix].append(route)
            
            # For each subnet, add the corresponding routes to the routing table
            # BUT in a specific subnet has multiple routes, append only the one with the lowest cost (best route possible)
            Logger().debug("\t *  adding routes to the routing table...")
            for _, possible_routes in routes.items():
                # Find the best route
                best_cost = float("inf")
                best_route = possible_routes[0]
                
                # If there are multiple routes, select the one with the lowest cost
                if len(possible_routes) > 1:
                    Logger().debug(f"\t [!] element {virt_element.get_name()} has {len(possible_routes)} routes to subnet {best_route.subnet.network_address()}. Selecting the one with the lowest cost...")
                    for route in possible_routes:
                        intf = route.via_interface.physical_interface
                        # Cast interface to RouterNetworkInterface to access cost
                        intf = cast(RouterNetworkInterface, intf)
                        if intf.get_cost() < best_cost:
                            best_cost = intf.get_cost()
                            best_route = route
                
                # Check if we have a marker on this route
                command_extra = ""

                # Check if the route has a marker
                for marker, routes in marker_lookup.items():
                    # Extract the route
                    marked_routes = [route for _, route in routes]
                    if best_route in marked_routes:
                        best_route.set_marker(marker)
                        Logger().debug(f"\t [!] element {virt_element.get_name()} has a marked route to subnet {best_route.subnet.network_address()}. Applying the marker rule...")
                        # Additional piece of code to apply the marker rule
                        command_extra = f" table {marker}"
                        # Save table lookup rule
                        executeCommand(node, f"ip rule add fwmark {marker} table {marker}")
                
                # Add the route to the routing table
                executeCommand(
                    node,
                    f"ip route add {best_route.subnet.network_address()}/{best_route.subnet.get_prefix_length()} via {best_route.dst_interface.physical_interface.get_ip()} dev {best_route.via_interface.name}{command_extra}",
                )
        
        # Mark the virtual network as started
        self._is_started = True
    
    @ensure_network_started
    def apply_traffic_control(self, flows_data: dict[Demand, TrafficEngineeringLPResult.FlowData], settings: TrafficControlSettings = _default_settings):
        # Traffic control parameters
        for demand, flow_data in flows_data.items():
            print(f"Flow from {demand.source.get_name()} to {demand.destination.get_name()} with {demand.maximumTransmissionRate} Mbps:")
            for src_node in flow_data.flow_path:
                print("\t *" + src_node.lp_route.src_element.get_name() + ":" + src_node.lp_route.route.via_interface.name + " -> " + src_node.lp_route.dst_element.get_name() + ":" + src_node.lp_route.route.dst_interface.name, " with capacity:", src_node.capacity, "Mbps")

        # For each demand, apply the traffic control rules to the corresponding interfaces
        for demand, flow_data in flows_data.items():
            print(f"Applying traffic control rules for demand {demand.source.get_name()} -> {demand.destination.get_name()} with {demand.maximumTransmissionRate} Mbps:")
            # Get all elements involved in the demand
            for path_node in flow_data.flow_path:
                # Get the Mininet node of the router
                src_node = self._net.get(path_node.lp_route.src_element.get_name())
                dst_node = self._net.get(path_node.lp_route.route.to_element.get_name())
                # Casting
                src_node = cast(Optional[Node], src_node)
                dst_node = cast(Optional[Node], dst_node)
                if src_node is None:
                    raise ValueError(
                            f"Node {path_node.lp_route.src_element.get_name()} not found in the virtual network. There is a problem with the network topology."
                    )
                if dst_node is None:
                    raise ValueError(
                            f"Node {path_node.lp_route.route.to_element.get_name()} not found in the virtual network. There is a problem with the network topology."
                    )

                # Extract information from traffic control settings
                burst = settings.get("burst", _default_settings["burst"])
                latency = settings.get("latency", _default_settings["latency"])
                min_burst = settings.get("min_burst", _default_settings["min_burst"])

                # Execute command on node to limit the bandwidth of the interface using a Token Bucket Filter (TBF)
                # NOTE: the actual bandwidth of the route is the capacity of the link
                executeCommand(src_node,
                            f"tc qdisc add dev {path_node.lp_route.route.via_interface.name} root "
                            f"tbf rate {path_node.capacity}mbit "
                            f"burst {int(burst[0])}{burst[1]} "
                            f"latency {int(latency[0])}{latency[1]} "
                            f"minburst {int(min_burst)}")
    def stop_network(self):
        """
        This method stops the virtual network and cleans up the Mininet environment.
        """
        if not self._is_started:
            raise NetworkError("The virtual network has not been started yet.")
        Logger().info("Stopping the virtual network...")
        self._net.stop()     
    
    def start_shell(self):
        """
        This method opens the Mininet CLI shell.
        """
        if not self._is_started:
            raise NetworkError("The virtual network has not been started yet.")
        Logger().info("Opening Mininet CLI shell...")
        CLI(self._net)
    
    def get_mininet(self) -> Mininet:
        """
        This method returns the Mininet object.
        """
        return self._net
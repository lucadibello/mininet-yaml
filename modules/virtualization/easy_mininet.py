from typing import Optional, cast
from mininet.net import Mininet

from mininet.node import Node
from mininet.cli import CLI
from modules.models.network_elements import NetworkElement, RouterNetworkInterface
from modules.models.topology import NetworkTopology
from modules.util.logger import Logger
from modules.util.mininet import executeChainedCommands, executeCommand
from modules.virtualization.network_elements import Route, VirtualNetwork, VirtualNetworkInterface

class EasyMininet():
    """
    Proxy class to simplify the usage of Mininet in the context of the virtual network representation generated from the YAML network definition.
    """
    
    def __init__(self, net: Mininet, physical_network: NetworkTopology, virtual_network: VirtualNetwork) -> None:
        self._net = net 
        self._physical_network = physical_network
        self._virtual_network = virtual_network

    def start_network(self):
        """
        This method starts the virtual network and configures the IP addresses and routing tables of all elements of the network
        according to the generated virtual network topology.
        """
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
            Logger().debug("\t * adding propagated routes to the routing table...")
            for _, possible_routes in routes.items():
                # Find the best route
                best_cost = float("inf")
                best_route = possible_routes[0]
                
                # If there are multiple routes, select the one with the lowest cost
                if len(possible_routes) > 1:
                    Logger().debug(f"\t [!] neighbor routers have propagated multiple routes for subnet {best_route.subnet.network_address()}. Selecting the one with the lowest cost...")
                    for route in possible_routes:
                        intf = route.via_interface.physical_interface
                        # Cast interface to RouterNetworkInterface to access cost
                        intf = cast(RouterNetworkInterface, intf)
                        if intf.get_cost() < best_cost:
                            best_cost = intf.get_cost()
                            best_route = route
                
                # Add the route to the routing table
                executeCommand(
                    node,
                    f"ip route add {best_route.subnet.network_address()}/{best_route.subnet.get_prefix_length()} via {best_route.dst_interface.physical_interface.get_ip()} dev {best_route.via_interface.name}",
                )
    
    def stop_network(self):
        """
        This method stops the virtual network and cleans up the Mininet environment.
        """
        Logger().info("Stopping the virtual network...")
        self._net.stop()     
    
    def start_shell(self):
        """
        This method opens the Mininet CLI shell.
        """
        Logger().info("Opening Mininet CLI shell...")
        CLI(self._net)
    
    def get_mininet(self) -> Mininet:
        """
        This method returns the Mininet object.
        """
        return self._net
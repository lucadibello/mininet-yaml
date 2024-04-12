from typing import Optional, cast
from modules.models.network_elements import NetworkElement
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Node
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.mininet import executeChainedCommands, executeCommand
from modules.virtualization.mininet_types import VirtualNetworkTopology
from modules.virtualization.network_elements import VirtualNetwork, VirtualNetworkInterface

            
def run_virtual_topology(network: NetworkTopology):
    # Create empty virtual network
    virtual_network = VirtualNetwork()

    # Cleanup any previous Mininet instances
    cleanup()

    # Start the virtual network passing the decoded network topology
    net = Mininet(
        topo=VirtualNetworkTopology(
            network=network, # pass decoded network topology
            virtual_network=virtual_network # pass store for virtual network elements (Mininet nodes + their virtual interfaces)
        ),
    )
    # Link the virtual network to the virtual network object
    virtual_network.set_network(net)

    # Start Mininet
    Logger().info("Starting the virtual network...")
    net.start()

    Logger().debug("Configuring IP addresses of the remaining unconfigured interfaces...")
                 
    # For each network element, configure the IP address of the virtual interfaces
    # FIXME: after implementing hosts this will become: network.get_routers() + network.get_hosts()
    for element in network.get_routers() + network.get_hosts():
        # cast element to NetworkElement
        element = cast(NetworkElement, element)
        
        # Get virtual node
        velement = virtual_network.get(element.get_name())
        if velement is None:
            raise ValueError(f"Virtual element {element.get_name()} not found in the virtual network. There is a problem with the network topology.")

        # Get virtual mininet node
        node = net.get(velement.get_name())
        node = cast(Optional[Node], node)
        if node is None:
            raise ValueError(f"Node {velement.get_name()} not found in the virtual network. There is a problem with the network topology.")

        # Get the virtual interfaces already configured
        vintfs = velement.get_virtual_interfaces()
        intfs = element.get_interfaces()
        
        # Configure the IP address of the missing virtual interfaces
        for intf in intfs:
            if not any(vintf.physical_interface.get_name() == intf.get_name() for vintf in vintfs):
                intf_name = element.get_name() + "-" + intf.get_name()
                Logger().warning(f"Interface {intf_name} of element {element.get_name()} is not used in any link. It will be created but kept down to avoid routing problems.")

                # Create the virtual interface and set the related IP address
                executeChainedCommands(node, [
                    f"ip link add {intf_name} type veth",
                    f"ifconfig {intf_name} {intf.get_ip()} netmask {intf.get_mask()}",
                    f"ifconfig {intf_name} down",
                ])

                # Register created interface in the virtual network object
                vintf = VirtualNetworkInterface(name=intf_name, physical_interface=intf)
                velement.add_virtual_interface(vintf)
                
    # Add default gateway for each element
    for virt_element in virtual_network.get_routers() + virtual_network.get_hosts():
        Logger().debug(f"Configuring routing table for element {virt_element.get_name()}")
        # Get mininet node
        node = net.get(virt_element.get_name())
        # cast to Node type (as Mininet does not specify any return type...)
        node = cast(Optional[Node], node)
        if node is None:
            raise ValueError(f"Element {virt_element.get_name()} not found in the virtual network. There is a problem with the network topology.")
 
        # Define which one is the default gateway for the network element
        gateway = virt_element.get_gateway()
        if gateway:
            # Now, add default gateway for the element in order to be able to reach subnets outside the ones it is directly connected to
            executeCommand(node, f"ip route add default via {gateway.ip}") 
        else:
            Logger().debug(f"\t [!] element {virt_element.get_name()} does not have a default gateway defined.") 
        
        # Now, for each route, add the corresponding route to the routing table
        for route in virt_element.get_routes():
            # For each unregistered route, add the route to the routing table
            if not route.is_registered:
                # Add the route to the routing table
                executeCommand(node, f"ip route add {route.subnet.network_address()}/{route.subnet.get_prefix_length()} via {route.dst_interface.physical_interface.get_ip()} dev {route.via_interface.name}")
 
    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()
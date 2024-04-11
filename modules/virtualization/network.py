from typing import Optional, cast
from modules.models.network_elements import NetworkElement 
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import Node, Intf
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.mininet import executeChainedCommands, executeCommand
from modules.virtualization.mininet_types import LinuxRouter, VirtualNetworkTopology
from modules.virtualization.network_elements import VirtualHost, VirtualNetwork, VirtualNetworkElement, VirtualNetworkInterface, VirtualRouter

            
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
        controller=None,
        build=True,
        autoSetMacs=True,
        waitConnected=True,
    )
    # Link the virtual network to the virtual network object
    virtual_network.set_network(net)

    # Start Mininet
    Logger().info("Starting the virtual network...")
    net.start()

    Logger().debug("Configuring IP addresses of the remaining virtual interfaces...")
                 
    # For each network element, configure the IP address of the virtual interfaces
    # FIXME: after implementing hosts this will become: network.get_routers() + network.get_hosts()
    for element in network.get_routers():
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
                Logger().debug(f"Creating missing virtual interface {intf_name} for element {element.get_name()}...")

                # Create the virtual interface and set the related IP address
                executeChainedCommands(node, [
                    f"ip link add {intf_name} type veth",
                    f"ifconfig {intf_name} {intf.get_ip()} netmask {intf.get_mask()}",
                    f"ifconfig {intf.get_name()} up",
                ])

                # Register created interface in the virtual network object
                vintf = VirtualNetworkInterface(name=intf_name, physical_interface=intf)
                velement.add_virtual_interface(vintf)
                
    # Create routing tables for the routers
    for virt_router in virtual_network.get_routers():
        Logger().debug(f"Configuring routing table for router {virt_router.get_name()}")
        
        # Get mininet node
        node = net.get(virt_router.get_name())
        # cast to Node type (as Mininet does not specify any return type...)
        node = cast(Optional[Node], node)
        if node is None:
            raise ValueError(f"Router {virt_router.get_name()} not found in the virtual network. There is a problem with the network topology.")
 
        # Define which one is the default gateway for the router
        gateway = virt_router.get_gateway()
        if gateway:
            # Now, add default gateway for the router in order to be able to reach subnets outside the ones it is directly connected to
            executeCommand(node, f"ip route add default via {gateway.ip}")

    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()
from typing import Optional, cast
from modules.models.network_elements import NetworkElement 
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.node import Node, Intf
from mininet.clean import cleanup

from modules.util.logger import Logger
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
                Logger().debug(f"Configuring IP address: {intf.get_ip()}/{intf.get_subnet().get_prefix_length()} for interface {intf_name}")

                
                # Create virtual interface
                # node.cmd(f"ip addr add {intf.get_ip()}/{intf.get_subnet().get_prefix_length()} type veth peer name {intf_name}")
                # node.cmd(f"ip link set {intf.get_name()} netns {element.get_name()}")
                # node.cmd(f"ip link set {intf.get_name()} up")

                # Get interfaces
                print(node.intfList())

                # Create intf 
                # node.addIntf(Intf(intf_name, node=node))
                # node.setIP(intf.get_ip(), intf.get_subnet().get_prefix_length(), intf=intf_name)

                # Register created interface in the virtual network object
                # vintf = VirtualNetworkInterface(name=intf_name, physical_interface=intf)
                # velement.add_virtual_interface(vintf)
                
    # Create routing tables for the routers
    for virt_router in virtual_network.get_routers():
        Logger().debug(f"Configuring routing table for router {virt_router.get_name()}")
        
        # Get mininet node
        node = net.get(virt_router.get_name())
        # cast to Node type (as Mininet does not specify any return type...)
        node = cast(Optional[Node], node)
        if node is None:
            raise ValueError(f"Router {virt_router.get_name()} not found in the virtual network. There is a problem with the network topology.")
 
        # Create entries for each subnet this router can reach
        for virt_intf in virt_router.get_virtual_interfaces():
            # Compute the subnet IP with prefix
            subnet_ip_with_prefix = f"{virt_intf.physical_interface.get_subnet().network_address()}/{virt_intf.physical_interface.get_subnet().get_prefix_length()}"
            # Write the command to add the route to the routing table
            command = f"ip route add {subnet_ip_with_prefix} dev {virt_intf.name}"
            # Execute the command + check for output (output = error message)
            asw = node.cmd(command)
            if asw:
                Logger().debug(f"\t - CMD: {command}, ERROR: {asw}")
            else:
                Logger().debug(f"\t - CMD: {command}, OK")
        
        # Define which one is the default gateway for the router
        gateway = virt_router.get_gateway()
        if gateway:
            cmd = f"ip route add default via {gateway.ip}"
            # Now, add default gateway for the router in order to be able to reach subnets outside the ones it is directly connected to
            asw = node.cmd(cmd)
            if asw:
                Logger().debug(f"\t - CMD: {cmd}, ERROR: {asw}")
            else:
                Logger().debug(f"\t - CMD: {cmd}, OK")

            # print(f"dev {gateway.interface.name} via {gateway.ip}")
            # node.setDefaultRoute(f"dev {gateway.interface.name} via {gateway.ip}")

    # Start the Mininet CLI
    CLI(net)
    # Once the CLI is closed, stop the virtual network
    net.stop()
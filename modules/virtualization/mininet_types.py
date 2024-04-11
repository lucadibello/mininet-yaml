from mininet.node import Node
from modules.models.network_elements import Router
from modules.models.topology import NetworkTopology

from mininet.topo import Topo

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet
from modules.virtualization.network_elements import Gateway, VirtualNetwork, VirtualNetworkInterface, VirtualRouter
from modules.exploration.explore import compute_routers_shortest_path


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class VirtualNetworkTopology(Topo): 

    def build(self, network: NetworkTopology, virtual_network: VirtualNetwork):
        """
        Virtualizes the network topology leveraging Mininet.

        Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

        Args:
            network (NetworkTopology): The network topology to virtualize.
        """

        Logger().info("Building the virtual network topology...")

        # Create mapping between virtual elements and Mininet nodes
        Logger().debug("Creating links between routers...")
        self._link_routers(network.get_routers(), virtual_network)
        
        # First of all, we need to create the virtual network by connecting together the virtual elements
        self._link_hosts(network.get_subnets(), virtual_network)
        
        # Notify that the topology has been constructed
        Logger().info("The virtual network topology has been built.")

    def _link_routers(self, routers: list[Router], virtual_network: VirtualNetwork):
        """This method connects routers together the best way possible, using the shortest path algorithm.
        This is necessary as we cannot connect the same interface to multiple routers, so we need to find the best way to connect them together.

        Args:
            routers (list[Router]): The list of routers to connect together.
        """
        # Check if we have at least two routers to connect
        if len(routers) < 2:
            return 

        # Compute shortest path between routers using Dijkstra
        _, previous = compute_routers_shortest_path(routers)

        # For each router, connect it to the previous one
        # If no previous router found, we can continue to the next one
        for router in routers: 
            # Find the best link between this router and the one before
            previous_router_link = previous.get(router, None)
            if previous_router_link is None:
                continue

            # Create the router object for the previous router (if not already created)
            for tmp in [router, previous_router_link.router]:
                if not virtual_network.has(tmp):
                    # Create the Mininet node describing the router
                    self.addHost(
                        tmp.get_name(),
                        cls=LinuxRouter,
                        ip=None # Avoid setting the default IP address
                    )
                    # Register virtual node in the virtual network object
                    virtual_network.add_router(VirtualRouter(tmp))
                    Logger().debug(f"Created virtual router: {tmp.get_name()}")

            # Create names for the routers interfaces
            src_intf_name = f"{router.get_name()}-{previous_router_link.via_interface.get_name()}" 
            dst_intf_name = f"{previous_router_link.router.get_name()}-{previous_router_link.destination_interface.get_name()}"

            # Connect the router to the previous one
            self.addLink(
                router.get_name(),
                previous_router_link.router.get_name(),
                intfName1=src_intf_name,
                params1={
                    'ip': previous_router_link.via_interface.get_ip_with_prefix()
                },
                intfName2=dst_intf_name,
                params2={
                    'ip': previous_router_link.destination_interface.get_ip_with_prefix()
                }
            )

            # Debug log that the link has been created
            Logger().debug(f"\t * created link: {router.get_name()}:{src_intf_name} <--> {previous_router_link.router.get_name()}:{dst_intf_name}")
            Logger().debug(f"\t\t IP: {previous_router_link.via_interface.get_ip_with_prefix()} <--> {previous_router_link.destination_interface.get_ip_with_prefix()}")

            # Find the virtual router objects and register the virtual interfaces
            src = virtual_network.get(router.get_name())
            dst = virtual_network.get(previous_router_link.router.get_name())
            
            # Check if actually they have been created
            if src is None or dst is None:
                raise ValueError("Virtual routers not found in the virtual network object. This should not happen.")

            # Create both virtual iterfaces
            src_vintf = VirtualNetworkInterface(
                name=src_intf_name,
                physical_interface=previous_router_link.via_interface
            )
            dst_vintf = VirtualNetworkInterface(
                name=dst_intf_name,
                physical_interface=previous_router_link.destination_interface
            )

            # Register the virtual interfaces used in the link
            src.add_virtual_interface(src_vintf)
            dst.add_virtual_interface(dst_vintf)

            # Set gateway for the source router: any subnet that it cannot reach will be sent to the destination router
            src.set_gateway(Gateway(
                ip=previous_router_link.destination_interface.get_ip(),
                via_interface_name=src_vintf.name
            ))

    def _link_hosts(self, subnets: list[Ipv4Subnet], virtual_network: VirtualNetwork):
        # Find subnets that interconnect hosts to routers
        for subnet in subnets:
            tot_hosts = len(subnet.get_hosts())
            tot_routers = len(subnet.get_routers())

            # If there are no hosts, this means that this subnet is used between routers. We can ignore it.
            if tot_hosts == 0:
                continue

            # Now that we have found a valid subnet, we must ensure that there is a router connected to it
            if tot_routers == 0:
                Logger().warning(f"No router present in subnet {subnet.network_address()}/{subnet.get_prefix_length()}. Cannot connect its hosts to the virtual network.")

            # Now, if we have only one host, we can connect it directly to the router without a switch
            if tot_hosts == 1:
                print("TODO: connect host directly to router")
            else:
                print("TODO: connect host to switch and switch to router")
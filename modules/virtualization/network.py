from typing import Sequence, cast
from modules.models.network_elements import Host, NetworkElement, Router
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.clean import cleanup

from modules.util.logger import Logger
from modules.util.network import Ipv4Subnet
from modules.virtualization.network_elements import VirtualHost, VirtualNetworkElement, VirtualNetworkInterface, VirtualRouter

from itertools import chain


class LinuxRouter(Node):
	def config(self, **params):
		super(LinuxRouter, self).config(**params)
		# Enable forwarding on the router
		self.cmd('sysctl net.ipv4.ip_forward=1')

	def terminate(self):
		self.cmd('sysctl net.ipv4.ip_forward=0')
		super(LinuxRouter, self).terminate()


def _exists_in_set(needle: tuple[str,str], haystack: set[tuple[str,str]]) -> bool:
	for item in haystack:
		if needle[0] == item[0] and needle[1] == item[1] or needle[0] == item[1] and needle[1] == item[0]:
			return True
	return False

class VirtualNetwork:
	def __init__(self):
		self._virtual_routers = list[VirtualRouter]()
		self._virtual_hosts = list[VirtualHost]()
		self._net: Mininet | None = None # type: ignore
		
	def set_network(self, net: Mininet):
		self._net = net

	def get_node(self, virtual_element: VirtualNetworkElement) -> Node:
		if not self._net:
			raise ValueError("The virtual network has not been linked to the Mininet instance yet!")
		# Force type cast to Node (Mininet node)
		return cast(Node, self._net.get(virtual_element.get_name()))
	
	def add_virtual_router(self, router: VirtualRouter):
		self._virtual_routers.append(router)
	
	def get_virtual_routers(self) -> list[VirtualRouter]:
		return self._virtual_routers

	def add_virtual_host(self, host: VirtualHost):
		self._virtual_hosts.append(host)
	

class VirtualNetworkTopology(Topo): 

	def _create_nodes(self, elements: Sequence[NetworkElement], **kwargs):
		for element in elements:
			# Create the node with the same name as the NetworkElement
			self.addHost(element.get_name(), ip=None, **kwargs)
			# Yield the element and the virtual element
			yield element

	def _link_routers(self, elements: Sequence[NetworkElement], virtual_elements_lookup_table: dict[NetworkElement, VirtualNetworkElement], added_links: set[tuple[str,str]]):
		for element in elements: 
			print()
			Logger().debug(f"Creating links for element {element.get_name()}. Found links: {len(element.get_links())}")
			 
			# Add all links connected to the current element
			for link in element.get_links():
				
				# Skip links that are connected to simple hosts as they have already been handled
				if isinstance(link.endpoint.entity, Host):
					continue
 
				# Create interface names
				source_nic_name = f"{element.get_name()}-{link.interface.get_name()}"
				destination_nic_name = f"{link.endpoint.entity.get_name()}-{link.endpoint.interface.get_name()}" 

				print("checking", (source_nic_name, destination_nic_name), added_links)

				# Get virtual elements
				virtual_source = virtual_elements_lookup_table[element]
				virtual_destination = virtual_elements_lookup_table[link.endpoint.entity]

				# Check if the link has already been found by other network elements
				if _exists_in_set((source_nic_name, destination_nic_name), added_links) or _exists_in_set((destination_nic_name, source_nic_name), added_links):
					Logger().info(f"\t [!] router link between {element.get_name()} (vintf: {source_nic_name}) and {link.endpoint.entity.get_name()} (vintf: {destination_nic_name}) already exist. Skipping...")
					continue

				# Register virtual interface names
				virtual_source.add_virtual_interface(VirtualNetworkInterface(
					source_nic_name,
					link.interface,
				))
				virtual_destination.add_virtual_interface(VirtualNetworkInterface(
					destination_nic_name,
					link.endpoint.interface,
				))

				# Create the link
				self.addLink(
					# Virtual source node name
					element.get_name(),
					# Virtual destination node name
					link.endpoint.entity.get_name(),

					# Source node link info
					intfName1=source_nic_name,
					params1={
						"ip": link.interface.get_ip_with_prefix()
					},

					# Destination node link info
					intfName2=destination_nic_name,
					params2={
						"ip": link.endpoint.interface.get_ip_with_prefix()
					}
				)
				
				# Add link to set
				added_links.add((source_nic_name, destination_nic_name))

				# Print the link
				Logger().info(f"\t * created link between {element.get_name()} (vintf: {source_nic_name}, ip: {link.interface.get_ip_with_prefix()}) and {link.endpoint.entity.get_name()} (vintf: {destination_nic_name}, ip: {link.endpoint.interface.get_ip_with_prefix()})")
		
	def _link_hosts_routers(self, subnets: Sequence[Ipv4Subnet], virtual_elements_lookup_table: dict[NetworkElement, VirtualNetworkElement], added_links: set[tuple[str,str]]):
		switch_counter=0
		for subnet in subnets:
			hosts = subnet.get_hosts()
			routers = subnet.get_routers()

			# If the subnet has only one host, a switch is not needed!
			if len(hosts) == 0: # subnet has no hosts
				Logger().warning(f"Subnet {subnet.get_ip()} does not have any valid host")
				continue

			if len(hosts) == 1: # subnet has only one host, connect directly to router
				host = hosts[0]
				for router in routers:
					# Get virtual element and register virtual interface name
					virtual_host = virtual_elements_lookup_table[host.entity]
					virtual_router = virtual_elements_lookup_table[router.entity]

					# Generate interface names
					host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}"
					router_intf_name = f"{router.entity.get_name()}-{router.interface.get_name()}"

					# Check if the link has already been found by other network elements
					if _exists_in_set((host_intf_name, router_intf_name), added_links):
						Logger().info(f"\t [!] link between {host.entity.get_name()} (vintf: {host_intf_name}) and {router.entity.get_name()} (vintf: {router_intf_name}) already exists. Skipping...")
						continue

					# Register virtual interface names
					virtual_router.add_virtual_interface(VirtualNetworkInterface(
						router_intf_name,
						router.interface,
					))
					virtual_host.add_virtual_interface(VirtualNetworkInterface(
						host_intf_name,
						host.interface,
					))	
 
					# Create the link
					self.addLink(
						host.entity.get_name(),
						router.entity.get_name(),
						# Source interface (Host)
						intfName1=host_intf_name,
						params1={
							"ip": host.interface.get_ip_with_prefix()
						},
						# Destination interface (Router)
						intfName2=router_intf_name,
						params2={
							"ip": router.interface.get_ip_with_prefix()
						},
					)
					added_links.add((host_intf_name, router_intf_name))
			else:
				# Generate a new management IP for the Switch in this particular subnet
				switch_ip = subnet.get_next_management_ip()
				switch_ip_with_prefix = f"{switch_ip}/{subnet.get_prefix_length()}"
				
				# Create the switch 
				switch = self.addSwitch(f"s{switch_counter}", cls=OVSKernelSwitch, failMode='standalone')

				# Increment the switch counter
				switch_counter += 1

				Logger().debug(f"Created switch {switch} for subnet {subnet.network_address()}")

				# Connect switch to all subnet routers
				for router in subnet.get_routers():
					# Generate interface names
					switch_intf_name = f"{switch}-eth0"
					router_intf_name = f"{router.entity.get_name()}-{router.interface.get_name()}"

					if _exists_in_set((switch_intf_name, router_intf_name), added_links):
						Logger().info(f"\t [!] link between switch {switch} (vintf: {switch_intf_name}) and router {router.entity.get_name()} (vintf: {router_intf_name}) already exists. Skipping...")
						continue

					# Register virtual interface names
					virtual_router = virtual_elements_lookup_table[router.entity]
					virtual_router.add_virtual_interface(VirtualNetworkInterface(
						router_intf_name,
						router.interface,
					))

					Logger().debug(f"\t * connecting router {router.entity.get_name()} (vintf: {router_intf_name}) to switch {switch} (vintf: {switch_intf_name})")
					self.addLink(
						switch,
						router.entity.get_name(),

						# Source interface (Switch)
						intfName1=switch_intf_name,
						params1={
							 "ip": switch_ip_with_prefix
						},
						
						# Destination interface (Router)
						intfName2=router_intf_name,
						params2={
							"ip": router.interface.get_ip_with_prefix()
						},
					)
					added_links.add((switch_intf_name, router_intf_name))

				# Connect the switch to all hosts in the subnet
				for host in subnet.get_hosts():
					# Generate interface names
					switch_intf_name = f"{switch}-eth1"
					host_intf_name = f"{host.entity.get_name()}-{host.interface.get_name()}"

					if _exists_in_set((switch_intf_name, host_intf_name), added_links):
						Logger().info(f"\t [!] link between {host.entity.get_name()} (vintf: {host_intf_name}) and switch {switch} (vintf: {switch_intf_name}) already exists. Skipping...")
						continue
					
					# Register virtual interface names
					virtual_host = virtual_elements_lookup_table[host.entity]
					virtual_host.add_virtual_interface(VirtualNetworkInterface(
						host_intf_name,
						host.interface,
					))

					Logger().debug(f"\t * connecting host {host.entity.get_name()} (vintf: {host_intf_name}) to switch {switch} (vintf: {switch_intf_name})")
					self.addLink(
						switch,
						host.entity.get_name(),
						# Source interface (Switch)
						intfName1=switch_intf_name,
						params1={
							"ip": switch_ip_with_prefix
						},
						
						# Destination interface (Host)
						intfName2=host_intf_name,
						params2={
							"ip": host.interface.get_ip_with_prefix()
						},
					)
					added_links.add((switch_intf_name, host_intf_name))

	def build(self, network: NetworkTopology, virtual_network: VirtualNetwork):
		"""
		Virtualizes the network topology leveraging Mininet.

		Some parts are inspired by the USI Mininet tutorial: https://www.inf.usi.ch/faculty/carzaniga/edu/adv-ntw/mininet.html

		Args:
			network (NetworkTopology): The network topology to virtualize.
		"""

		Logger().info("Building the virtual network topology...")

		virtual_elements_lookup_table = dict[NetworkElement, VirtualNetworkElement]()
		added_links = set()

		# Create empty nodes for each router and host
		for element in chain(
			self._create_nodes(network.get_routers(), cls=LinuxRouter),
			self._create_nodes(network.get_hosts())
		):
			# Check if the element is a router or a host
			if isinstance(element, Router):
				virtual_router = VirtualRouter(physical_router=element)
				virtual_network.add_virtual_router(virtual_router)
				# Register element in lookup table
				virtual_elements_lookup_table[element] = virtual_router
			else: # then it is a host
				virtual_host = VirtualHost(physical_host=element)
				virtual_network.add_virtual_host(virtual_host)
				# Register element in lookup table
				virtual_elements_lookup_table[element] = virtual_router


		# Create all links between routers
		self._link_routers(network.get_routers(), virtual_elements_lookup_table, added_links)
		print()

		# For each subnet, create a switch (if needed) and connect hosts to routers
		self._link_hosts_routers(network.get_subnets(), virtual_elements_lookup_table, added_links)
			
def run_virtual_topology(network: NetworkTopology):
	# Create empty virtual network
	virtual_network = VirtualNetwork()
	# Before starting the virtual network, clean up any previous Mininet instances
	cleanup()
	try:
		# Start the virtual network passing the decoded network topology
		net = Mininet(topo=VirtualNetworkTopology(network=network, virtual_network=virtual_network), controller=None)
		# Link the virtual network to the virtual network object
		virtual_network.set_network(net)
		# Start the virtual network
		Logger().info("Starting the virtual network...")
		net.start()

		Logger().info("Network topology virtualized successfully! Configuring routing tables...")

		# Build routing table for each virtual router in the network
		for virtual_router in virtual_network.get_virtual_routers():
			# Build the routing table for the router
			Logger().debug(f"Configuring routing table for {virtual_router.get_physical_element().get_name()}...")
			for virtual_interface in virtual_router.get_virtual_interfaces():
				# Get the Mininet node object
				node = virtual_network.get_node(virtual_router)

				# FIXME: Devo fare in modo che il virtual router venga creato con le virtual interface corrette. 
				# Non vanno i comandi successivi siccome noi andiamo a leggere il nome delle physical interfaces e non delle virtual interfaces
	
				# Add the route to the routing table
				output = node.cmd(f"ip route add {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} dev {virtual_interface.name}")
				if output:
					Logger().warning(f"Failed to add route to {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} on {virtual_interface.name}. Error: {output}")
				else:
					Logger().debug(f"Added route to {virtual_interface.physical_interface.get_subnet().network_address()} via {virtual_interface.physical_interface.get_ip()} on {virtual_interface.name}")
		
		Logger().info("Routing tables configured successfully! Starting the Mininet CLI...")
		
		# Start the Mininet CLI
		CLI(net)
		# Once the CLI is closed, stop the virtual network
		net.stop()
	except Exception as e:
		Logger().fatal(f"Failed to virtualize the network topology. {str(e)}")

from typing import Sequence, cast
from modules.models.network_elements import (
    Demand,
    Link,
    NetworkElement,
    Host,
    Router,
    RouterNetworkInterface,
)
from modules.util.logger import Logger
from modules.util.network import Ipv4Network, Ipv4Subnet, does_link_exist


class NetworkTopology:
    """
    This class represents the network topology of the virtual network
    """

    def __init__(self, routers: list[Router], hosts: list[Host], demands: list[Demand] = []):
        self._routers = routers
        self._hosts = hosts
        self._demands = demands

        # keep track of all the subnets in the network and the network elements that are part of them
        self._subnets: list[Ipv4Subnet] = []
        self._subnets_ids: dict[str, int] = {}

        _total_links = 0

        # Find and create all the links between routers and hosts
        _total_links += NetworkTopology._create_links(self._routers, self._hosts)
        # Find links between routers
        _total_links += NetworkTopology._create_links(self._routers, self._routers)

        # Save total number of unique links
        self._total_links = _total_links

        # Create subnets
        self._create_subnets(self._routers, are_routers=True)
        self._create_subnets(self._hosts)

        # Check for any routers or hosts that are not linked to any other network element
        for router in self._routers:
            if not router.get_links():
                Logger().warning(
                    f"Router {router.get_name()} "
                    "is not linked to any other network element."
                )
        for host in self._hosts:
            if not host.get_links():
                Logger().warning(
                    f"Host {host.get_name()} "
                    "is not linked to any other network element."
                )

    @staticmethod
    def _create_links(
        set_a: Sequence["NetworkElement"], set_b: Sequence["NetworkElement"]
    ) -> int:
        # Find all the links between routers and hosts
        total_links = 0
        for a in set_a:
            for b in set_b:
                # If for any reason the two network elements are the same, skip as they cannot be linked
                if (
                    a.get_name() == b.get_name()
                ):  # Skip if the two network elements are the same
                    continue

                # Compute all possible links between the two network elements
                found, interfaces = does_link_exist(a, b)
                if not found:
                    continue

                # Add the link between the two elements
                for source_interface, destination_interface in interfaces:
                    total_links += 1

                    # If the cost between the two network elements is not the same, raise a warning
                    if isinstance(
                        source_interface, RouterNetworkInterface
                    ) and isinstance(destination_interface, RouterNetworkInterface):
                        if (
                            source_interface.get_cost()
                            != destination_interface.get_cost()
                        ):
                            Logger().info(
                                f"Found cost discrepancy between "
                                f"{a.get_name()}"
                                f"(inet: {source_interface.get_name()}, "
                                f"cost {source_interface.get_cost()}) and "
                                f"{b.get_name()}"
                                f"(inet: {destination_interface.get_name()}, "
                                f"cost: {destination_interface.get_cost()}). "
                                f"Overriding cost to "
                                f"{source_interface.get_cost()}."
                            )
                            destination_interface.set_cost(source_interface.get_cost())

                    # Create links
                    source_to_destination = Link(
                        source_interface,
                        Link.Endpoint(entity=b, interface=destination_interface),
                    )
                    destination_to_source = Link(
                        destination_interface,
                        Link.Endpoint(entity=a, interface=source_interface),
                    )

                    # Add the links to the network elements if they do not exist
                    if not a.has_link(source_to_destination):
                        a.add_link(source_to_destination)
                    if not b.has_link(destination_to_source):
                        b.add_link(destination_to_source)

        # Return total amount of unique links
        return total_links

    def _create_subnets(
        self, elements: Sequence[NetworkElement], are_routers: bool = False
    ):
        # Now, for each element, check if it is part of a subnet by analyzing all the interfaces
        for element in elements:
            for intf in element.get_interfaces():
                # Get the network IP of the interface
                network_ip = Ipv4Network(
                    intf.get_ip(), intf.get_mask()
                ).network_address()

                # Create a new subnet object
                if network_ip not in self._subnets_ids:
                    # Create a new subnet object
                    subnet = Ipv4Subnet(network_ip, intf.get_mask())

                    # Add the element to the subnet
                    if are_routers:
                        subnet.add_router(Link.Endpoint(entity=element, interface=intf))
                    else:
                        subnet.add_host(Link.Endpoint(entity=element, interface=intf))

                    # Add subnet to the list of subnets
                    self._subnets.append(subnet)


                    # Register the subnet ID for fast lookup
                    self._subnets_ids[network_ip] = len(self._subnets) - 1
                else:
                    # If the subnet already exists, update the subnet object with the new element
                    idx = self._subnets_ids[network_ip]

                    endpoint = Link.Endpoint(entity=element, interface=intf)

                    if are_routers:
                        self._subnets[idx].add_router(endpoint)
                    else:
                        self._subnets[idx].add_host(endpoint)

        # Log for each subnet the elements that are part of it
        for subnet in self._subnets:
            Logger().debug(f"Subnet {subnet.get_ip()}/{subnet.get_prefix_length()} contains:")
            for router in subnet.get_routers():
                Logger().debug(f"\tRouter {router.entity.get_name()} via {router.interface.get_name()}")
            for host in subnet.get_hosts():
                Logger().debug(f"\tHost {host.entity.get_name()} via {host.interface.get_name()}")

    def draw(self):
        """
        This method returns a string containing a GraphViz representation of the network topology.
        It includes only Routers and shows the cost of the links between them.
        """
        graph = "graph network {\n"

        # Increase node + rank separation
        graph += "\tnodesep=1.0;\n"  # Needed to enhance visibility
        graph += "\tranksep=1.0;\n"  # Needed to avoid overlapping edges

        # Total number of routers
        tot_routers = len(self._routers)

        # Sort the routers by name to keep the indexing consistent
        self._routers.sort(key=lambda x: x.get_name())

        # Create hashmap to get the index of a router by its name in O(1)
        router_index = {
            router.get_name(): index for index, router in enumerate(self._routers)
        }

        # 3D adjacency matrix to store the edges between routers, and cost of the link between them
        adj_matrix: list[list[list[int]]] = [
            [list() for _ in range(tot_routers)] for _ in range(tot_routers)
        ]

        def get_index(router: Router):
            return router_index[router.get_name()]

        def create_edge(
            source: Link.Endpoint,
            destination: Link.Endpoint,
            cost: int,
            label_distance: float = 0.5,
        ) -> str:
            return (
                f"\t{source.entity.get_name()} -- {destination.entity.get_name()} "
                "["
                f'label="{cost}", '
                "\n\t\tfontsize=8, "
                f"\n\t\tlabeldistance={label_distance}, "
                f'\n\t\theadlabel="{source.interface.get_name()}", '
                f'\n\t\ttaillabel="{destination.interface.get_name()}", '
                '\n\t\tstyle="solid", '
                "\n\t\tcolor=black, "
                "\n\t\tpenwidth=1, "
                "\n\t\tfontcolor=black, "
                '\n\t\tfontname="Arial", '
                "\n\t\tfontsize=8"
                "];\n"
            )

        # Created nodes for each router
        for router in self._routers:
            graph += f"\t{router.get_name()} [shape=circle, color=blue];\n"

        # For each router, create an edge to each destination router
        for source in self._routers:
            for link in source.get_links():
                # Unpack values
                source_interface = link._interface
                destination = link._endpoint

                # Ensure both ends are router
                if not isinstance(destination.entity, Router):
                    continue

                # Register the edge in the adjacency matrix
                source_index = get_index(source)
                destination_index = get_index(destination.entity)

                # Cast to RouterNetworkInterface to access cost
                link_cost = cast(RouterNetworkInterface, source_interface).get_cost()

                # Check if the edge should be added to the graph
                if (
                    len(adj_matrix[source_index][destination_index]) == 0
                    or link_cost not in adj_matrix[source_index][destination_index]
                ):
                    # Add the edge to the graph
                    graph += create_edge(
                        Link.Endpoint(source, source_interface), destination, link_cost
                    )
                    # Append the edge to the adjacency matrix (undirected graph)
                    adj_matrix[source_index][destination_index].append(link_cost)
                    adj_matrix[destination_index][source_index].append(link_cost)
                else:
                    Logger().debug(
                        f"Edge between {source.get_name()} and "
                        f"{destination.entity.get_name()} already exists. "
                        "Skipping."
                    )

        graph += "}"
        return graph

    def __str__(self):
        return f"NetworkTopology(routers={self._routers}, hosts={self._hosts})"

    def __repr__(self):
        return self.__str__()

    def get_routers(self):
        return self._routers

    def get_hosts(self):
        return self._hosts

    def get_total_links(self):
        return self._total_links

    def get_subnets(self):
        return self._subnets

    def get_demands(self):
        return self._demands
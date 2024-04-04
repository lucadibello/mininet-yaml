from typing import Sequence, cast
from modules.models.network_elements import NetworkElement, Host, Link, Router, RouterNetworkInterface
from modules.util.logger import Logger
from modules.util.network import does_link_exist


class NetworkTopology:
    """
    This class represents the network topology of the virtual network
    """

    def __init__(self, routers: list[Router], hosts: list[Host]):
        self._routers = routers
        self._hosts = hosts

        _total_links = 0

        # Find and create all the links between routers and hosts
        _total_links += NetworkTopology._create_links(
            self._routers, self._hosts)
        # Find links between routers
        _total_links += NetworkTopology._create_links(
            self._routers, self._routers)
        # Find links between hosts
        _total_links += NetworkTopology._create_links(self._hosts, self._hosts)

        # Check if there are some network elements that are not linked to any other network element
        for router in self._routers:
            if not router.get_links():
                Logger().warning(
                    f"Router {router.get_name()} is not linked to any other network element."
                )
        for host in self._hosts:
            if not host.get_links():
                Logger().warning(
                    f"Host {host.get_name()} is not linked to any other network element."
                )

        # Save total number of unique links
        self._total_links = _total_links

    @staticmethod
    def _create_links(
            set_a: Sequence["NetworkElement"], set_b: Sequence["NetworkElement"]
    ) -> int:
        # Find all the links between routers and hosts
        total_links = 0
        for a in set_a:
            for b in set_b:
                # If for any reason the two network elements are the same, skip as they cannot be linked
                if a.get_name() == b.get_name():
                    continue

                # Compute all possible links between the two network elements
                found, interfaces = does_link_exist(a, b)
                if not found:
                    continue

                # Add the link between the two elements
                for source_interface, destination_interface in interfaces:
                    total_links += 1

                    # Create link between the two network elements
                    link = Link(
                        source=Link.Endpoint(
                            entity=a, interface=source_interface),
                        destination=Link.Endpoint(
                            entity=b, interface=destination_interface
                        ),
                    )

                    # Add the link to the source network element
                    a.add_link(link)
                    # Add the link to the destination network element
                    b.add_link(link)

        # Return total amount of unique links
        return total_links

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
        router_index = {router.get_name(): index for index,
                        router in enumerate(self._routers)}

        # 3D adjacency matrix to store the edges between routers, and cost of the link between them
        adj_matrix: list[list[list[int]]] = [
            [list() for _ in range(tot_routers)] for _ in range(tot_routers)]

        def get_index(router):
            return router_index[router.get_name()]

        def create_edge(source: Link.Endpoint, destination: Link.Endpoint, cost: int,
                        label_distance: float = .5) -> str:
            return (
                f'\t{source.entity.get_name()} -- {destination.entity.get_name()} '
                '['
                f'label="{cost}", '
                '\n\t\tfontsize=8, '
                f'\n\t\tlabeldistance={label_distance}, '
                f'\n\t\theadlabel=" {source.interface.get_name()}", taillabel=" {destination.interface.get_name()}", '
                '\n\t\tstyle="solid", '
                '\n\t\tcolor=black, '
                '\n\t\tpenwidth=1, '
                '\n\t\tfontcolor=black, '
                '\n\t\tfontname="Arial", '
                '\n\t\tfontsize=8'
                '];\n'
            )

        # Created nodes for each router
        for router in self._routers:
            graph += f"\t{router.get_name()} [shape=circle, color=blue];\n"

        # For each router, create an edge to each destination router
        for router in self._routers:
            for link in router.get_links():
                # Unpack values
                source = link.get_source()
                destination = link.get_destination()

                # Ensure both ends are routers
                if (not isinstance(source.entity, Router) or not isinstance(destination.entity, Router)):
                    continue

                # Register the edge in the adjacency matrix
                source_index = get_index(source.entity)
                destination_index = get_index(destination.entity)

                # Cast to RouterNetworkInterface to access cost
                link_cost = cast(RouterNetworkInterface,
                                 source.interface).get_cost()

                # Check if the edge should be added to the graph
                if (len(adj_matrix[source_index][destination_index]) == 0 or link_cost not in adj_matrix[source_index][destination_index]):
                    # Add the edge to the graph
                    graph += create_edge(source, destination, link_cost)
                    # Append the edge to the adjacency matrix (undirected graph)
                    adj_matrix[source_index][destination_index].append(
                        link_cost)
                    adj_matrix[destination_index][source_index].append(
                        link_cost)
                else:
                    Logger().debug(
                        f"Edge between {source.entity.get_name()} and {destination.entity.get_name()} already exists."
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

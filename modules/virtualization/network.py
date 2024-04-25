from typing import Tuple
from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.clean import cleanup

from modules.virtualization.easy_mininet import EasyMininet
from modules.virtualization.virtual_topology import VirtualNetworkTopology
from modules.virtualization.network_elements import VirtualNetwork


def create_network_from_virtual_topology(network: NetworkTopology) -> Tuple[EasyMininet, VirtualNetwork]:
    # Create empty virtual network
    virtual_network = VirtualNetwork()

    # Cleanup any previous Mininet instances
    cleanup()

    # Start the virtual network passing the decoded network topology
    net = Mininet(
        topo=VirtualNetworkTopology(
            network=network,  # pass decoded network topology
            # pass store for virtual network elements (Mininet nodes + their virtual interfaces)
            virtual_network=virtual_network,
        ),
    )
    # Link the virtual network to the virtual network object
    virtual_network.set_network(net)

    # Return the EasyMininet wrapper and the virtual network
    return EasyMininet(net, network, virtual_network), virtual_network

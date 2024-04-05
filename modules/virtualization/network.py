from modules.models.topology import NetworkTopology

from mininet.net import Mininet
from mininet.node import Controller


def virtualize_network(network: NetworkTopology) -> None:
    """
    Virtualizes the network topology leveraging Mininet.

    Args:
        network (NetworkTopology): The network topology to virtualize.
    """

    # Create empty network
    net = Mininet(controller=Controller)

    # Add rotuers to the network
    for router in network.get_routers():
        net.addHost(router.get_name(), ip=f"{router.get_ip()}/{router.get_subnet()}")
    pass

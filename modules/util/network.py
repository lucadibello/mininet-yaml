class Ipv4Network:
    def __init__(self, ip: str, mask: str):
        self._ip = ip
        self._mask = mask

    def to_binary(self) -> str:
        """
        This method converts the IPv4 network to its binary representation.
        """
        return "".join([bin(int(x) + 256)[3:] for x in self._ip.split(".")])

    def network_address(self) -> str:
        """
        This method returns the network address of the IPv4 network by applying the subnet mask.
        """
        return ".".join(
            str(int(x) & int(y))
            for x, y in zip(self._ip.split("."), self._mask.split("."))
        )

    @staticmethod
    def can_communicate(a: "Ipv4Network", b: "Ipv4Network") -> bool:
        """
        This method checks if two IPv4 addresses can communicate with each other.
        """
        return a.network_address() == b.network_address()

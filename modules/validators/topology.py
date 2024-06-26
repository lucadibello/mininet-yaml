import ipaddress
from typing import Tuple, cast

from modules.models.network_elements import (
    NetworkInterface,
    Router,
    Host,
    RouterNetworkInterface,
    NetworkElementDemand,
    Demand,
)

_FIELDS = ["routers", "hosts"]


def _validate_network_element_name(name: str) -> Tuple[bool, str]:
    """
    This function is used to validate the name of any kind of network topology specification element (router/host).
    """
    # Check for null value or empty string
    if not name:
        return False, "The name cannot be empty."
    # Check if the name is alphanumeric
    if not name.isalnum():
        return False, "The name must be alphanumeric."
    # Name must not match regex s[0-9]+
    if name[0] == "s" and name[1:].isdigit():
        return (
            False,
            "The router/host name must not match the regex 's[0-9]+' as it is reserved for switches.",
        )
    return True, ""


def _validate_interface_name(name: str) -> Tuple[bool, str]:
    if not name:
        return False, "The name cannot be empty."
    if not name.startswith("eth"):
        return False, "The interface name must start with 'eth'."
    if not name[3:].isdigit():
        return False, "The interface name must end with a number."
    return True, ""


def _validate_network_interface_details(data: dict[str, str]) -> Tuple[bool, str]:
    # Check for null value or empty string
    if not data:
        return False, "The interface details cannot be empty."
    # Check if the address is valid
    address = data.get("address")
    if not address:
        return False, "The address cannot be empty."
    try:
        ipaddress.IPv4Address(address)
    except ValueError:
        return False, "The address is not a valid IPv4 address."
    # Check if the mask is valid
    mask = data.get("mask")
    if not mask:
        return False, "The mask cannot be empty."
    try:
        ipaddress.IPv4Network(f"0.0.0.0/{mask}", strict=False)
    except ValueError:
        return False, "The mask is not a valid subnet mask."
    return True, ""


def validate_configuration_structure(data: dict[str, dict]) -> Tuple[bool, str]:
    if not isinstance(data, dict) or len(data) == 0:
        return False, "Input data should be a non-empty dictionary."
    for field in _FIELDS:
        if (
            field not in data
            or not isinstance(data[field], dict)
            or len(data[field].keys()) == 0
        ):
            return False, f"Field '{field}' is missing or empty."
    return True, ""


def _validate_router_network_interface_details(
    data: dict[str, str],
) -> Tuple[bool, str]:
    # First, validate generic field
    status, msg = _validate_network_interface_details(data)
    if not status:
        return status, msg

    # Then, validate cost (if present)
    if data.get("cost") and not isinstance(data["cost"], int):
        return False, "The cost must be a positive integer."

    # Finally, return success
    return True, ""


def validate_routers(data: dict[str, dict]) -> Tuple[list[Router], bool, str]:
    # Read router names
    names = data.keys()

    # Ensure that the router names are unique
    if len(names) != len(set(names)):
        return [], False, "Router names must be unique!"

    # Keep track of all routers
    routers = []

    # Now, ensure also that all router names do not match any switch names
    for name in names:
        # First, validate name
        status, msg = _validate_network_element_name(name)
        if not status:
            return [], status, msg

        # Ensure that router data still exists (avoid type hint errors)
        router_details = data.get(name)
        if router_details is None:
            return (
                [],
                False,
                f"Could not find any interfaces for the router {name} in the configuration.",
            )

        # Create router
        router = Router(name)

        # Now, get all the interfaces for the router
        interfaces = router_details.items()

        # Then, get all the interfaces for the router
        for interface_name, interface_details in interfaces:
            # Validate the interface name
            status, msg = _validate_interface_name(interface_name)
            if not status:
                return [], False, f"{msg} (router {name})"

            # Validate fields
            status, msg = _validate_router_network_interface_details(interface_details)
            if not status:
                return [], False, f"{msg} (router {name}, interface {interface_name})"

            # Convert to a RouterNetworkINterface object
            interface = RouterNetworkInterface(
                interface_name,
                interface_details["address"],
                interface_details["mask"],
                interface_details.get("cost", 1),
            )

            # Append interface to router
            router.add_interface(interface)

        # Add router to list
        routers.append(router)

    # Return parsed routers to the caller
    return routers, True, ""


def validate_hosts(data: dict[str, dict]) -> Tuple[list[Host], bool, str]:
    # Read host names
    names = data.keys()

    # Ensure that the host names are unique
    if len(names) != len(set(names)):
        return [], False, "Host names must be unique!"

    # Keep track of all hosts
    hosts = []

    # Now, ensure also that all router names do not match any switch names
    for name in names:
        # First, validate name
        status, msg = _validate_network_element_name(name)
        if not status:
            return [], status, msg

        # Ensure that router data still exists (avoid type hint errors)
        host_details = data.get(name)
        if host_details is None:
            return (
                [],
                False,
                f"Could not find any interfaces for the host {name} in the configuration.",
            )

        # Create host
        host = Host(name)

        # Now, get all the interfaces for the router
        interfaces = host_details.items()

        # Then, get all the interfaces for the router
        for interface_name, interface_details in interfaces:
            # Validate the interface name
            status, msg = _validate_interface_name(interface_name)
            if not status:
                return [], False, f"{msg} (host {name})"

            # Validate fields
            status, msg = _validate_network_interface_details(interface_details)
            if not status:
                return [], False, f"{msg} (host {name}, interface {interface_name})"

            # Convert to a RouterNetworkINterface object
            interface = NetworkInterface(
                interface_name, interface_details["address"], interface_details["mask"]
            )
            # Append interface to router
            host.add_interface(interface)

        # Append host to hosts list
        hosts.append(host)

    # Return parsed hosts to the caller
    return hosts, True, ""


def validate_network_configuration(
    routers: list[Router], hosts: list[Host]
) -> Tuple[bool, str]:
    # Acquire all IP addresses from the network configuration
    ip_addresses = []
    masks = []
    for router in routers:
        ip_addresses.extend(interface.get_ip() for interface in router.get_interfaces())
        masks.extend(interface.get_mask() for interface in router.get_interfaces())
    for host in hosts:
        ip_addresses.extend(interface.get_ip() for interface in host.get_interfaces())
        masks.extend(interface.get_mask() for interface in host.get_interfaces())

    # Check for duplicate IP addresses
    if len(ip_addresses) != len(set(ip_addresses)):
        return (
            False,
            "There are duplicate IP addresses in the network configuration. Each network interface must have a unique IP address.",
        )

    # Now, for each IP address, check if it is within a valid subnet
    for ip, mask in zip(ip_addresses, masks):
        try:
            ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
        except ValueError:
            return (
                False,
                f"The IP address {ip} is not within a valid subnet.",
            )

    return True, ""


def validate_demands(
    raw_demands: list[dict], hosts: list[Host], routers: list[Router]
) -> Tuple[list[Demand], bool, str]:
    # Check if the demands are empty
    if len(raw_demands) == 0:
        return [], False, "No demands were found in the configuration."

    # keep track of created demands
    demands = list[Demand]()

    # For each demand, extract the required fields
    for raw_demand in raw_demands:
        if not all(field in raw_demand for field in ["src", "dst", "rate"]):
            return [], False, "A demand must have the fields 'src', 'dst', and 'rate'."

        # If src and dst are the same, return an error
        if raw_demand["src"] == raw_demand["dst"]:
            return [], False, "Source and destination of a demand cannot be the same."

        # Validate all fields
        src_name = raw_demand["src"].strip()
        dst_name = raw_demand["dst"].strip()
        rate = raw_demand["rate"]

        # Look for the source and destination in the network elements
        # If not found, return an error
        src, dst = None, None
        for element in hosts + routers:
            if element.get_name() == src_name:
                src = element
            if element.get_name() == dst_name:
                dst = element

            if src is not None and dst is not None:
                break

        # Notify the user if the source or destination is not found
        if src is None:
            return [], False, f"Source {src_name} of demand not found."
        if dst is None:
            return [], False, f"Destination {dst_name} of demand not found."

        # Rate must be a positive float
        if not isinstance(rate, int) or rate <= 0:
            return [], False, "Rate must be a positive integer (> 0)."

        # Create the demand object
        demand = Demand(src, dst, rate)

        # Record the demand in the global array
        demands.append(demand)

        # Assign the demand to both elements
        demand = cast(NetworkElementDemand, demand)
        src.add_demand(demand)
        dst.add_demand(demand)

    # Return success + all the created demands
    return demands, True, ""

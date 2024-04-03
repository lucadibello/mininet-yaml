import ipaddress
from typing import Tuple

from modules.models.topology import (
    NetworkInterface,
    Router,
    Host,
    RouterNetworkInterface,
)

_FIELDS = ["routers", "hosts"]


def _validate_network_element_name(name: str) -> Tuple[bool, str]:
    """
    This function is used to validate the name of the network element.
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
            not data[field]
            or not isinstance(data[field], dict)
            or len(data[field].keys()) == 0
        ):
            return False, f"Field '{field}' is missing or empty."
    return True, ""


def _validate_router_network_interface_details(
    data: dict[str, str]
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
        print(hex(id(host)), host)
        hosts.append(host)

    # Return parsed hosts to the caller
    return hosts, True, ""


def validate_network_configuration(
    routers: list[Router], hosts: list[Host]
) -> Tuple[bool, str]:
    ip_addresses = []
    for router in routers:
        [
            ip_addresses.append(interface.get_ip())
            for interface in router.get_interfaces()
        ]
    test = []
    for host in hosts:
        [test.append(interface.get_ip()) for interface in host.get_interfaces()]

    print(ip_addresses)
    print(test)

    if len(ip_addresses) != len(set(ip_addresses)):
        return (
            False,
            "There are duplicate IP addresses in the network configuration. Each network interface must have a unique IP address.",
        )
    return True, ""

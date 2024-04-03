import yaml

from modules.models.topology import NetworkTopology
from modules.util.exceptions import ValidationError
from modules.validators.topology import (
    validate_configuration_structure,
    validate_routers,
    validate_hosts,
)


def decodeTopology(file_path: str) -> NetworkTopology:
    """
    This file reads, parses and validates the YAML file containing the network topology and returns the parsed data as a dictionary.

    Parameters:
    file_path (str): The path to the YAML file containing the network definition.

    Returns:
    dict: The parsed data from the YAML file.

    Raises:
    ValueError: If the YAML file is not valid or cannot be parsed.
    """
    # Read the YAML file
    data = None
    with open(file_path, "r") as file:
        try:
            data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error while parsing the YAML file: {e}")
    if not data:
        raise ValueError("Empty YAML file provided.")

    try:
        status, msg = validate_configuration_structure(data)
        if not status:
            raise ValueError(f"Error while validating the YAML file: {msg}")

        # Now, validate the routers
        routers, status, msg = validate_routers(data["routers"])
        if not status:
            raise ValueError(f"Error while validating the YAML file: {msg}")

        # Now, validate the hosts
        hosts, status, msg = validate_hosts(data["hosts"])
        if not status:
            raise ValueError(f"Error while validating the YAML file: {msg}")

        # Build network topology
        return NetworkTopology(routers=routers, hosts=hosts)
    except ValidationError as e:
        raise ValueError(f"Invalid YAML file: {e}")

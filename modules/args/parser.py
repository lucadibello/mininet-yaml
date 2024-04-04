import argparse
from modules.validators.args import ValidateYAMLPath, ValidateDirectoryPath


class ArgParser:
    def __init__(self):
        # usage: emulation.py [-h] [-d] definition
        self._parser = argparse.ArgumentParser(
            description="This tool is able to read a network definition from a YAML file and either draw the network topology as a graph or create a virtual network leveraging Mininet."
        )
        # YAML file path
        self._parser.add_argument(
            "definition",
            help="path to the YAML file containing the network definition",
            # Custom validator that checks if the file exists and is readable
            action=ValidateYAMLPath,
        )
        # Draw mode
        self._parser.add_argument(
            "-d",
            "--draw",
            help="output to stdout the router topology as a graph in graphviz format",
            action="store_true",
        )
        # Log directory
        self._parser.add_argument(
            "-l",
            "--log",
            help="directory to store the log files",
            # Custom validator that checks if the directory exists and is writable
            action=ValidateDirectoryPath,
            required=False,
        )
        # Add verbose flag
        self._parser.add_argument(
            "-v",
            "--verbose",
            help="enable verbose logging",
            action="store_true",
            required=False,
        )
        # Add silent flag
        self._parser.add_argument(
            "-s",
            "--silent",
            help="disable all logging to stdout, except for critical errors",
            action="store_true",
            required=False,
        )

    def parse(self):
        try:
            # Return the parsed arguments
            return self._parser.parse_args()
        except ValueError as e:
            # In case of errors, print the error message and exit
            self._parser.error(str(e))

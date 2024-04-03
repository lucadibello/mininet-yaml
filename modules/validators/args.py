import argparse
from typing import Any


class ValidateDirectoryPath(argparse.Action):
    """
    This class is used by argparse to validate the path to the directory passed as an argument by the user.
    """

    def __call__(self, parser, namespace, values, option_string=None) -> Any:
        """
        This method is called by argparse to validate the path to the directory.
        """
        path = values
        # Convert the path to a string
        if not isinstance(path, str):
            path = str(path)
        # Check for null value or empty string
        if not path:
            raise ValueError("The directory path cannot be empty.")
        # Check if directory exists
        try:
            with open(path, "r"):
                pass
        except FileNotFoundError:
            raise ValueError("The directory does not exist.")
        except PermissionError:
            raise ValueError("The directory is not writable.")

        # Set the path to the directory
        setattr(namespace, self.dest, path)


class ValidateYAMLPath(argparse.Action):
    """
    This class is used by argparse to validate the path to the YAML file passed as an argument by the user.
    """

    def __call__(self, parser, namespace, values, option_string=None) -> Any:
        """
        This method is called by argparse to validate the path to the YAML file.
        """
        path = values
        # Convert the path to a string
        if not isinstance(path, str):
            path = str(path)
        # Check for null value or empty string
        if not path:
            raise ValueError("The file path cannot be empty.")
        # Check if file has right extension
        if not path.endswith(".yaml"):
            raise ValueError("The file must be a YAML file.")
        # Check if file exists and is readable
        try:
            with open(path, "r"):
                pass
        except FileNotFoundError:
            raise ValueError("The file does not exist.")
        except PermissionError:
            raise ValueError("The file is not readable.")

        # Set the path to the YAML file
        setattr(namespace, self.dest, path)

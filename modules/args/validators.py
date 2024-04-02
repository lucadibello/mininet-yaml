import argparse
from typing import Any

class ValidatePath(argparse.Action):
  '''
  This class is used by argparse to validate the path to the YAML file passed as an argument by the user.
  '''
  
  def __call__(self, parser, namespace, values, option_string=None) -> Any:
    '''
    This method is called by argparse to validate the path to the YAML file.
    '''
    path = values
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
    
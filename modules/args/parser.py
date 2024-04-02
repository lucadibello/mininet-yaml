import argparse
from .validators import ValidatePath


class ArgParser:
	def __init__(self):
		# usage: emulation.py [-h] [-d] definition
		self._parser = argparse.ArgumentParser(description="This tool is able to read a network topology written in YAML and emulate it using Mininet.")
		# YAML file path
		self._parser.add_argument(
			"definition",
			help="path to the YAML file containing the network definition",
			action=ValidatePath # Custom validator that checks if the file exists and is readable
		)
		# Draw mode
		self._parser.add_argument(
			"-d", "--draw",
			help="output the network topology in a GraphViz format",
			action="store_true"
		)

	def parse(self):
		try:
			# Return the parsed arguments
			return self._parser.parse_args()
		except ValueError as e:
			# In case of errors, print the error message and exit
			self._parser.error(str(e))
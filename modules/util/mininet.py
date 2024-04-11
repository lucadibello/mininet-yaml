from mininet.node import Node

from modules.util.logger import Logger


def executeCommand(node: Node, command: str) -> bool:
    asw = node.cmd(command)
    if asw:
        Logger().debug(f"\t - CMD: {command}, ERROR: {asw}")
        return False
    else:
        Logger().debug(f"\t - CMD: {command}, OK")
        return True

def executeChainedCommands(node: Node, commands: list) -> bool:
    for command in commands:
        if not executeCommand(node, command):
            return False
    return True
# Mininet-YAML <!-- omit in toc -->

<div style="width: 100%; display: block;">
    <p align="center">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="./docs/assets/logo/logo-dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="./docs/assets/logo/logo-light.svg">
            <img alt="Mininet-YAML logo" src="./doc/logo/logo-light.svg" />
        </picture>
    </p>
</div>

<p align="center"><strong>🛜 Instantly Create and Manage Virtual Networks on your machine through Simple YAML Configurations</strong></p>


## Introduction

Mininet-YAML is a powerful tool that simplifies the creation of virtual networks through YAML-configured topologies. By defining hosts, routers, and their interfaces in a YAML file, users can deploy complex network topologies within seconds. This tool integrates with [Mininet](https://mininet.org/) and [Open vSwitch](https://www.openvswitch.org/) to emulate network environments, allowing users to manage virtual nodes with the same granularity as physical hardware.

## Features

- **Rapid Network Deployment**: Generate a complete virtual network from a YAML file, automating connections and configurations.
- **Intuitive Topology Visualization**: Outputs a visual representation of your network in Graphviz format directly to your terminal.
- **Routing Tables Propagation**: Automatically configures routing tables and propagates them across the network in order to enable communication between all nodes.
- **Multi-interface Nodes**: Supports complex setups with hosts and routers having multiple network interfaces.
- **Link cost configuration**: Allows users to set the cost of a particular interface, an information used by the routing algorithm to determine the best path.
- **Error Handling**: Provides detailed error messages during YAML file validation, virtual network creation, and runtime.
- **Fine-grained logging and silent mode**: Offers verbose logging for debugging purposes and a silent mode to suppress output (useful for scripting).
- **Interactive CLI**: Offers a command-line interface to interact with network elements, enhancing manual testing and management.
- **Custom Commands and scripts**: Allows users to run custom commands and scripts directly on virtual nodes.
- **GUI Application Support**: Enables X11 forwarding to launch and use GUI-based applications on virtual hosts as if they were physical machines.
- **Extensive Command Execution**: Facilitates running network diagnostic tools like `ping`, `traceroute`, and `wireshark` within virtual nodes.

## Getting started

Please, refer to the [Getting Started](./docs/getting-started.md) guide to learn how to install the tool and run your first network.

## Tool usage

Via `emulation.py`, users can either draw the network topology as a graph or create a virtual network leveraging Mininet. The tool accepts the following arguments:

```text
usage: emulation.py [-h] [-d] [-l LOG] [-v] [-s] definition

This tool is able to read a network definition from a YAML file and either draw the network topology as a graph or
create a virtual network leveraging Mininet.

positional arguments:
  definition         path to the YAML file containing the network definition

options:
  -h, --help         show this help message and exit
  -d, --draw         output the router topology as an undirected graph in Graphviz format
  -l LOG, --log LOG  specify the directory where the log file will be saved (default: logs/)
  -v, --verbose      enable verbose logging
  -s, --silent       disable all logging to stdout, except for critical errors
```

## Defining Topologies

Below is the structure required in the YAML file to define your network's topology:

```yaml
routers:
  [router_name]:
    [interface_name]:
      address: [ipv4_ip_address]
      mask: [subnet_mask]
      cost: [cost, default=1]
    ...

hosts:
  [host_name]:
    [interface_name]:
      address: [ip_address]
      mask: [subnet_mask]
    [interface_name]:
      address: [ip_address]
      mask: [subnet_mask]
    ...
```

## Use cases

- **Testing**: Verify network configurations and experiment with different topologies without physical setups.
- **Education**: Demonstrate networking concepts interactively, giving students hands-on experience with network management.
- **Development**: Design and test network applications in a safe and controlled virtual environment.
- **Research**: Explore and test new networking protocols or configurations with ease.

## Examples

In the directory [`examples`](./examples), you can find some YAML files that define different network topologies. You can use them to test the tool and understand how to define your own network.

## Development environment

To simplify the development process, this repository includes a preconfigured Devcontainer (available in directory [`.devcontainer`](./.devcontainer)) that includes all the necessary tools and dependencies to develop and test the tool.

It follows the open specification of development containers (refer to [Development Containers - Specification](https://containers.dev/implementors/spec/), hence it is supported by Visual Studio Code and other IDEs that support this standard.

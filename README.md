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

Mininet-YAML is a powerful tool that simplifies the creation of virtual networks through YAML-configured topologies. By defining hosts, routers, and their interfaces in a YAML file, users can deploy complex network topologies directly on their machines within seconds. This tool integrates with [Mininet](https://mininet.org/) and [Open vSwitch](https://www.openvswitch.org/) to emulate network environments, allowing users to manage virtual nodes with the same granularity as physical hardware.

Moreover, Mininet-YAML empowers users with advanced traffic engineering capabilities. They can effortlessly specify maximum transmission rates (goodput) between nodes, triggering automatic adjustments to network link capacities and routing table entries to achieve desired goodput levels. Leveraging a Mixed Integer Linear Programming (MILP) model solved by the [CBC Solver](http://www.coin-or.org/Cbc/), this tool ensures optimal network performance tailored to user specifications.

## Features

🚀 **Rapid Network Deployment**: 
- Generate a complete virtual network from a YAML file, automating connections and configurations.

📊 **Intuitive Topology Visualization**: 
- Outputs a visual representation of your network in Graphviz format directly to your terminal.

🌐 **Routing Tables Propagation**: 
- Automatically configures routing tables and propagates them across the network to enable communication between all nodes.

🛠️ **Goodput-based Traffic Engineering**: 
- Automatically adjusts link capacities and routing tables to achieve a desired goodput between two nodes.

🔄 **Multi-interface Nodes**: 
- Supports complex setups with hosts and routers having multiple network interfaces.

💰 **Link cost configuration**: 
- Allows users to set the cost of a particular interface, used by the routing algorithm to determine the best path.

❌ **Error Handling**: 
- Provides detailed error messages during YAML file validation, virtual network creation, and runtime.

📝 **Fine-grained logging and silent mode**: 
- Offers verbose logging for debugging purposes and a silent mode to suppress output.

💻 **Interactive CLI**: 
- Provides a command-line interface to interact with network elements, enhancing manual testing and management.

📜 **Custom Commands and scripts**: 
- Allows users to run custom commands and scripts directly on virtual nodes.

🖥️ **GUI Application Support**: 
- Enables X11 forwarding to launch and use GUI-based applications on virtual hosts.

🛠️ **Extensive Command Execution**: 
- Facilitates running network diagnostic tools like `ping`, `traceroute`, and `wireshark` within virtual nodes.

## Getting started

Please, refer to the [Getting Started](./docs/getting-started.md) guide to learn how to install the tool and run your first network.

## Tool usage

Via `emulation.py`, users can either draw the network topology as a graph or create a virtual network leveraging Mininet. The tool accepts the following arguments:

```text
usage: emulation.py [-h] [-d] [-l] [-p] [-ld LOG_DIR] [-v] [-s] definition

This tool is able to read a network definition from a YAML file and either draw the network topology as a graph or create a virtual network leveraging Mininet.

positional arguments:
  definition            path to the YAML file containing the network definition

optional arguments:
  -h, --help            show this help message and exit
  -d, --draw            output to stdout the router topology as an undirected graph in Graphviz format
  -l, --lp              output to stdout the network engineering optimization problem in CPLEX format generated from the specified demands in the YAML file
  -p, --print           output to stdout the optimal goodput archievable for each of the flows listed in the demands in the YAML file (if any)
  -ld LOG_DIR, --log-dir LOG_DIR
                        specify the directory where the log file will be saved (default: logs/)
  -v, --verbose         enable verbose logging
  -s, --silent          disable all logging to stdout, except for critical errors
```

## Defining Topologies

The Mininet-YAML tool facilitates the creation of virtual networks by reading network topologies defined in a YAML file. This file configuration allows you to specify the structure of routers, hosts, their respective interfaces, and optionally, maximum goodput demands for enhanced traffic engineering.

### Structure of the YAML file

#### Routers

Each router is defined by a name and includes one or more interfaces. Interfaces are detailed with IP addresses, subnet masks, and optionally, costs which influence routing decisions or traffic engineering.

```yaml
routers:
  router_name:
    interface_name:
      address: ipv4_ip_address
      mask: subnet_mask
      cost: cost_value  # Optional; default is 1
```

#### Hosts

Similar to routers, each host is defined with a unique name and configured with one or more network interfaces:

```yaml
hosts:
  host_name:
    interface_name:
      address: ip_address
      mask: subnet_mask
```

#### Demands (optional)

If your topology requires specific traffic management, the `demands` section allows you to define the maximum goodput demands between hosts. This section triggers traffic engineering functionalities where the tool adjusts link capacities and routing configurations to meet these demands.

### Functionality of Interface Costs

The cost assigned to each interface serves dual purposes:

1. **Routing Algorithm**: The routing algorithm utilizes the cost to determine the optimal path between nodes. A lower cost generally makes a path more favorable.

2. **Traffic Engineering**: When the demands section is included, the cost influences the adjustment of link capacities and routing tables to achieve the specified goodput, integrating a strategic layer to network management.

> **Note**: Absence of the `demands` section defaults the cost utility to only influence routing decisions.

## Examples

In the directory [`examples`](./examples), you can find some YAML files that define different network topologies. You can use them to test the tool and understand how to define your own network.

### Example 1: Simple dumbbell network

This example defines a simple dumbbell network with two routers and two hosts. The routers are connected to each other, and each host is connected to one of the routers. This is the topology built by the Mininet-YAML tool:

IMAGE!

> YAML configuration file available in [`examples/dumbell-network-no-cost.yaml`](./examples/dumbell-network-no-cost.yaml)

### Example 2: Complex network with multiple routers and hosts

This example defines a more complex network with 3 routers, 4 hosts, and multiple links between them. Each router has 3 interfaces, in which some have a connection. The cost of each link is used by the routing algorithm to determine the best path.

`Mininet-YAML` will automatically add switches where necessary. This is the topology built by the Mininet-YAML tool:

IMAGE!

> YAML configuration file available in [`examples/complex-network-multilink-with-costs.yaml`](./examples/complex-network-multilink-with-costs.yaml)


### Example 3: Complex network with multiple routers, hosts and demands

Thix 

> YAML configuration file available in [`examples/network-with-demands.yaml`](./examples/network-with-demands.yaml)

## Development environment

To simplify the development process, this repository includes a preconfigured Devcontainer (available in directory [`.devcontainer`](./.devcontainer)) that includes all the necessary tools and dependencies to develop and test the tool.

It follows the open specification of development containers (refer to [Development Containers - Specification](https://containers.dev/implementors/spec/), hence it is supported by Visual Studio Code and other IDEs that support this standard.

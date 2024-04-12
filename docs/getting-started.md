# Getting started

This guide will help you to install the tool and run your first network.

## Requirements

- Python 3.6 or higher
- `pip` (Python package manager) or `conda` (Anaconda package manager)

## Step 1: Install Mininet and Open vSwitch

First of all, you need to install `Mininet` on your system. Follow the instructions [here](./docs/install-mininet.md).

Then, we need to install also `Open vSwitch` on your system. Follow the instructions [here](./docs/install-ovs.md).

## Step 2: Clone the repository

You can clone the repository using `git`:

```bash
# With SSH
git clone git@github.com:lucadibello/mininet-yaml.git && cd mininet-yaml
# With HTTPS
git clone https://github.com/lucadibello/mininet-yaml.git && cd mininet-yaml
```

## Step 2: Install python requirements

To install the required Python packages, you can either use `pip` (to install the packages globally) or use `conda` (preferred method) to create a virtual environment and install the packages locally.

Option A: Using `conda`:

```bash
# Create virtual environment + install packages
conda env create --file=environment.yml
# Activate the virtual environment
conda activate mininet-yaml
```

Option B: Using `pip`:

```bash
# Install the required packages
pip install -r requirements.txt
```

## Step 3: Run the tool

Finally, you can run the tool by providing the path to the YAML file with the network topology description. To test the tool, you can use one of the examples provided in the `examples` directory. For example:

```bash
python emulation.py examples/complex-network-multilink-with-costs.yaml
```

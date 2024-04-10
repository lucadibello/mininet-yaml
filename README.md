# Mininet-YAML

This small tool allows creating virtual network using [Mininet](https://mininet.org/) by providing a network topology description in YAML format.

## Getting started

First of all, you need to install `Mininet` on your system. Follow the instructions [here](./docs/install.md).

Then you need to install the required Python packages. You can do this by running the following command:

```bash
pip install -r requirements.txt
```

Finally, you can run the tool by providing the path to the YAML e file with the network topology description. For example:

```bash
python main.py topology.example.yaml
```

## Things to do

- [ ] Add default gateway to the hosts (hosts have only one interface, so the default gateway is the first one)
- [ ] Create algorithm that chooses which interface to connect to the switch and which to other routers
- [ ] Configure routing tables in the Routers (static routing)
- [ ] Rename switches ports properly: switch connection to router = `s-eth0`, host input ports = `s-eth<N_HOST>`

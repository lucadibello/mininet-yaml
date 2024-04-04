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

# Install Open vSwitch on your system

Open vSwitch is a production-quality, multilayer virtual switch licensed under the open-source Apache 2.0 license. It is designed to enable massive network automation through programmatic extension, while still supporting standard management interfaces and protocols (e.g., NetFlow, sFlow, SPAN, RSPAN, CLI, LACP, 802.1ag). Open vSwitch can operate both as a soft switch running within the hypervisor and as the control stack for switching silicon.

The following tutorial will guide you through the installation of Open vSwitch on your Debian-based system. For other systems, please refer to the [official Open vSwitch website](https://www.openvswitch.org/).

## Step 1: Install Open vSwitch package

First, update the package list and install the Open vSwitch package:

```bash
sudo apt update
sudo apt install openvswitch-switch openvswitch-common
```

## Step 2: Start Open vSwitch service

After the installation, start the Open vSwitch service:

```bash
sudo systemctl start openvswitch-switch
```

To enable the Open vSwitch service to start automatically at boot time, run:

```bash
sudo systemctl enable openvswitch-switch
```

## Step 3: Verify the installation

To verify that Open vSwitch is correctly installed and running, you can use the following command:

```bash
sudo ovs-vsctl show
```
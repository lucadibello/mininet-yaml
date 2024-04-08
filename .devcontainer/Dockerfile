FROM mcr.microsoft.com/devcontainers/anaconda:0-3

COPY ./environment.yml /tmp/environment.yml

# install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends mininet iputils-ping iproute2 net-tools iperf3 openvswitch-switch

# Create environment from file
RUN /opt/conda/bin/conda env create -f /tmp/environment.yml

# Change shell command
SHELL ["/bin/bash", "-c"]

# Initialize conda
RUN conda init bash
# Now, change the UMASK
RUN umask 0002
# Activate environment
RUN source /opt/conda/bin/activate mininet-yaml
# Permanently activate environment
RUN echo "source /opt/conda/bin/activate mininet-yaml" >> ~/.bashrc
# Delete environment file
RUN rm /tmp/environment.yml

# Start OpenvSwitch serviec
RUN service openvswitch-switch start

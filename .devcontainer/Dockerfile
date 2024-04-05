FROM mcr.microsoft.com/devcontainers/anaconda:0-3

COPY ./environment.yml /tmp/environment.yml

# Create environment from file
RUN /opt/conda/bin/conda env create -f /tmp/environment.yml
RUN /opt/conda/bin/conda init
# Activate environment
RUN /opt/conda/bin/activate mininet-yaml
# Permanently activate environment
RUN echo "/opt/conda/bin/activate mininet-yaml" >> ~/.bashrc
# Delete environment file
RUN rm /tmp/environment.yml

# install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends mininet

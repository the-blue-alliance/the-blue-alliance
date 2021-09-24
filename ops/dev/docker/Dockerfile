FROM --platform=linux/x86_64 ubuntu:latest
MAINTAINER The Blue Alliance

# Set debconf to run non-interactively
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Get base system dependencies
RUN apt-get update && apt-get install -y \
  wget \
  curl \
  unzip \
  sudo \
  jq \
  tmux \
  vim \
  openssh-server \
  redis-server

# Setup python environmenets
# python3 should be the default, but gcloud currently depends on python2
RUN apt-get install -y \
    python3-pip \
    python3-venv \
    python2 \
    python-dev
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN echo 1 | update-alternatives --config python

# Add gcloud repository and Cloud SDK dependencies
RUN apt-get update && apt-get install -y apt-transport-https curl
RUN echo "deb https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
RUN apt-get update && apt-get install -y \
    google-cloud-sdk \
    google-cloud-sdk-app-engine-python \
    google-cloud-sdk-app-engine-python-extras \
    google-cloud-sdk-datastore-emulator \
    google-cloud-sdk-pubsub-emulator

# Set up nvm and nodejs
ENV NVM_DIR /nvm
ENV NODE_VERSION 14
RUN mkdir -p $NVM_DIR  \
    && wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION --silent \
    && nvm alias default $NODE_VERSION \
    && nvm use default --silent

# Install pip2 for gcloud dependencies
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py | python2

# Configure ssh server
RUN mkdir /var/run/sshd
RUN echo 'root:tba' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22

# Expose ports for TBA
EXPOSE 8000
EXPOSE 8080-8089
EXPOSE 9181

# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]

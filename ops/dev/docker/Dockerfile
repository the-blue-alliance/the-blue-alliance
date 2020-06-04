FROM ubuntu:latest
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
  openssh-server

# Setup python environmenets
# python3 should be the default, but gcloud currently depends on python2
RUN apt-get install -y \
    python3-pip \
    python3-venv \
    python2
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN echo 1 | update-alternatives --config python

# Add gcloud repository and Cloud SDK dependencies
RUN apt-get update && apt-get install -y apt-transport-https curl
RUN echo "deb https://packages.cloud.google.com/apt cloud-sdk-xenial main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
RUN apt-get update && apt-get install -y \
    google-cloud-sdk \
    google-cloud-sdk-app-engine-python \
    google-cloud-sdk-app-engine-python-extras \
    google-cloud-sdk-datastore-emulator \
    google-cloud-sdk-pubsub-emulator

# Install nodejs
RUN apt-get install -y nodejs npm

# Install pip2 for gcloud dependencies
RUN curl https://bootstrap.pypa.io/get-pip.py | python2

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

# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]

FROM ubuntu:24.04
LABEL maintainer="The Blue Alliance"

# Set debconf to run non-interactively
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Get base system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    unzip \
    sudo \
    jq \
    tmux \
    vim \
    openssh-server

RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y

# Setup python environment
ENV PYTHON_VERSION=python3.13
RUN apt-get update && apt-get install -y \
    "$PYTHON_VERSION" \
    "$PYTHON_VERSION-venv" \
    "$PYTHON_VERSION-dev"
RUN update-alternatives --install /usr/bin/python python "/usr/bin/$PYTHON_VERSION" 1
RUN update-alternatives --install /usr/bin/python3 python3 "/usr/bin/$PYTHON_VERSION" 1
RUN echo 1 | update-alternatives --config python
RUN echo 1 | update-alternatives --config python3

# The ubuntu python3-pip package depends on distutils, which is not available in Python 3.13
# So we install pip manually using get-pip.py
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

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
ENV HTTPLIB2_CA_CERTS="/usr/lib/google-cloud-sdk/platform/google_appengine/lib/httplib2/httplib2/cacerts.txt"

# Install JDK for firebase-tools
RUN apt-get update && apt-get install default-jre -y

# Set up nvm and nodejs
ENV NVM_DIR=/nvm
ENV NODE_VERSION=24
RUN mkdir -p $NVM_DIR  \
    && wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION --silent \
    && nvm alias default $NODE_VERSION \
    && nvm use default --silent

# Configure ssh server
RUN mkdir /var/run/sshd
RUN echo 'root:tba' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE="in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22

# Expose Firebase emulator
EXPOSE 4000
EXPOSE 4400
EXPOSE 4500
EXPOSE 9005
EXPOSE 9000
EXPOSE 9099

# Expose ports for TBA
EXPOSE 8000
EXPOSE 8080-8089

# Pre-install Python dependencies (layer cached until lockfiles change)
# Build context must be the repo root (context: ./ with file: ops/dev/docker/Dockerfile).
RUN python -m pip config set global.break-system-packages true \
    && pip install --upgrade setuptools uv
COPY pyproject.toml uv.lock /tmp/tba-deps/
RUN cd /tmp/tba-deps \
    && uv export --no-dev --no-hashes --frozen -o requirements.txt \
    && pip install --ignore-installed -r requirements.txt \
    && rm -rf /tmp/tba-deps

# Pre-install Node dependencies (layer cached until package-lock.json changes)
COPY package.json package-lock.json /tmp/tba-node-deps/
# Copy local file dependencies referenced in package.json
COPY src/frontend/lib/ /tmp/tba-node-deps/src/frontend/lib/
RUN . $NVM_DIR/nvm.sh \
    && cd /tmp/tba-node-deps \
    && npm ci --legacy-peer-deps \
    && npm install -g firebase-tools \
    && npm install -g uglify-js@3.17.4 \
    && rm -rf /tmp/tba-node-deps

# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]

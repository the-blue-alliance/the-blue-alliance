#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# Update system dependencies
# Skip apt-get upgrade on CI - the Docker image is already up-to-date
# and this saves ~2 minutes downloading package updates
if [ -z "$CI" ]; then
    apt-get update && apt-get upgrade -y
fi

# The datastore emulator requires grpcio
# On CI, pip dependencies are pre-installed in the Docker image
if [ -z "$CI" ]; then
    python -m ensurepip --upgrade
    pip install --upgrade setuptools
    pip install --ignore-installed -r requirements.txt
    pip install --ignore-installed -r src/requirements.txt
fi

# Create empty keys file if one does not already exist
if [ ! -f /tba/src/backend/web/static/javascript/tba_js/tba_keys.js ]; then
    cp /tba/src/backend/web/static/javascript/tba_js/tba_keys_template.js /tba/src/backend/web/static/javascript/tba_js/tba_keys.js
fi

# nodejs dependencies
NVM_DIR="/nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use default
# skip puppeteer chromium install on aarch64 or CI
if [ "$(uname -m)" = "aarch64" ] || [ -n "$CI" ]; then
    export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
    export PUPPETEER_SKIP_DOWNLOAD=true
fi

echo "Running npm install... this may take a while..."
npm ci

# Install the Firebase tools for the Firebase emulator
# On CI, these are pre-installed in the Docker image
if [ -z "$CI" ]; then
    npm install -g firebase-tools
    npm install -g uglify-js@3.17.4
fi

./ops/build/run_buildweb.sh

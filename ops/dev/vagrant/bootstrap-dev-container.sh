#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# Update system dependencies
apt-get update && apt-get upgrade -y

# The datastore emulator requires grpcio
python -m ensurepip --upgrade
pip install --upgrade setuptools
pip install --ignore-installed -r requirements.txt
pip install --ignore-installed -r src/requirements.txt

# Create empty keys file if one does not already exist
if [ ! -f /tba/src/backend/web/static/javascript/tba_js/tba_keys.js ]; then
    cp /tba/src/backend/web/static/javascript/tba_js/tba_keys_template.js /tba/src/backend/web/static/javascript/tba_js/tba_keys.js
fi

# nodejs dependencies
NVM_DIR="/nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use default
# skip puppeteer chromium install on aarch64
if [ "$(uname -m)" = "aarch64" ]; then
    export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
fi

echo "Running npm install... this may take a while..."
npm ci

# Install the Firebase tools for the Firebase emulator
npm install -g firebase-tools
npm install -g uglify-js@3.17.4

./ops/build/run_buildweb.sh

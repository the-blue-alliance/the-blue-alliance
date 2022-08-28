#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# The datastore emulator requires grpcio
python -m pip install --upgrade pip
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
npm install

# Install the Firebase tools for the Firebase emulator
npm install -g firebase-tools

./ops/build/run_buildweb.sh

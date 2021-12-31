#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# The datastore emulator requires grpcio
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r src/requirements.txt

# nodejs dependencies
NVM_DIR="/nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use default
npm install

# Install the Firebase tools for the Firebase emulator
npm install -g firebase-tools

./ops/build/run_buildweb.sh

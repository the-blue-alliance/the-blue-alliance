#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# System packages are already current at Docker image build time.
# Skipping apt-get update/upgrade to avoid ~60s of unnecessary work.

python -m pip config set global.break-system-packages true
pip install --upgrade setuptools uv
uv export --no-dev --no-hashes --frozen -o src/requirements.txt
# --ignore-installed is needed because some system packages (e.g. pyparsing)
# were installed via apt and lack pip metadata, causing uninstall errors.
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
command -v firebase >/dev/null 2>&1 || npm install -g firebase-tools

./ops/build/run_buildweb.sh

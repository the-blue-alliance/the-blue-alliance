#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# Create empty keys file if one does not already exist
if [ ! -f /tba/src/backend/web/static/javascript/tba_js/tba_keys.js ]; then
    cp /tba/src/backend/web/static/javascript/tba_js/tba_keys_template.js /tba/src/backend/web/static/javascript/tba_js/tba_keys.js
fi

# If dependencies changed since image was built, reinstall them
# This handles the case where the image is outdated
if [ -f /tba/package.json ]; then
    echo "Checking for dependency updates..."

    # Check if node_modules is missing or package-lock has changed
    if [ ! -d /tba/node_modules ] || ! cmp -s /tba/package-lock.json /tmp/.image-package-lock.json 2>/dev/null; then
        echo "Installing Node dependencies..."
        NVM_DIR="/nvm"
        # shellcheck source=/dev/null
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm use default
        npm ci
        cp /tba/package-lock.json /tmp/.image-package-lock.json 2>/dev/null || true
    fi

    # Check if Python dependencies changed
    if ! cmp -s /tba/pyproject.toml /tmp/.image-pyproject.toml 2>/dev/null; then
        echo "Installing Python dependencies..."
        python -m pip config set global.break-system-packages true
        pip install --upgrade setuptools uv
        uv export --no-dev --no-hashes --frozen -o src/requirements.txt
        pip install --ignore-installed -r src/requirements.txt
        cp /tba/pyproject.toml /tmp/.image-pyproject.toml 2>/dev/null || true
    fi
fi

# Always run webpack build (it's relatively fast and ensures assets are up-to-date)
./ops/build/run_buildweb.sh

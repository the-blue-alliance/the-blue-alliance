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
    if [ ! -d /tba/node_modules ] || ! cmp -s /tba/package-lock.json /image-build-context/package-lock.json 2>/dev/null; then
        # Check if node_modules exists in image build context and can be copied
        if [ -d /image-build-context/node_modules ] && cmp -s /tba/package-lock.json /image-build-context/package-lock.json 2>/dev/null; then
            echo "Copying Node dependencies from Docker image..."
            cp -r /image-build-context/node_modules /tba/
        else
            echo "Installing Node dependencies..."
            NVM_DIR="/nvm"
            # shellcheck source=/dev/null
            [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
            nvm use default
            npm ci
        fi
    else
        echo "Skipping Node install (dependencies unchanged)"
    fi

    # Check if Python dependencies changed from what was used to build the image
    if ! cmp -s /tba/pyproject.toml /image-build-context/pyproject.toml 2>/dev/null ||
        ! cmp -s /tba/uv.lock /image-build-context/uv.lock 2>/dev/null; then
        echo "Installing Python dependencies..."
        python -m pip config set global.break-system-packages true
        pip install --upgrade setuptools uv
        uv export --no-dev --no-hashes --frozen -o src/requirements.txt
        pip install --ignore-installed -r src/requirements.txt
    else
        echo "Skipping Python install (dependencies unchanged from Docker image)"
        # Still need to generate requirements.txt for dev_appserver
        uv export --no-dev --no-hashes --frozen -o src/requirements.txt
    fi
fi

# Run webpack build if assets don't exist or not in CI
# In CI, assets are pre-built on the host to speed up container startup
if [ ! -d "/tba/src/build" ] || [ "${CI:-}" != "true" ]; then
    echo "Building webpack assets..."
    ./ops/build/run_buildweb.sh
else
    echo "Skipping webpack build (assets pre-built in CI)"
fi

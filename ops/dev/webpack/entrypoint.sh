#!/bin/sh
set -e

# Create empty keys file if one does not already exist
if [ ! -f src/backend/web/static/javascript/tba_js/tba_keys.js ]; then
    cp src/backend/web/static/javascript/tba_js/tba_keys_template.js \
        src/backend/web/static/javascript/tba_js/tba_keys.js
fi

# Skip npm ci if node_modules is already installed and package-lock.json has not changed
if [ ! -d node_modules ] || [ "${FORCE_NPM_INSTALL}" = "true" ] || [ package-lock.json -nt node_modules ]; then
    echo "Installing node dependencies..."
    npm ci --prefer-offline --no-audit --no-fund
else
    echo "node_modules already exists, skipping npm ci."
fi

# Run webpack in watch mode (dev) or one-shot build (CI/deploy)
if [ "${WATCH}" = "true" ]; then
    # Watch legacy JS files for changes and recompress in the background
    # (--watch does an initial build before entering the watch loop)
    uv run --group webpack python3 ./ops/build/do_compress.py --watch &
    echo "Starting webpack in watch mode..."
    npm run dev
else
    # Build legacy concatenated JS bundles
    uv run --group webpack python3 ./ops/build/do_compress.py
    if [ "${WEBPACK_ENV:-development}" = "production" ]; then
        echo "Running production webpack build..."
        npm run build
    else
        echo "Running development webpack build..."
        npm run build:dev
    fi
fi

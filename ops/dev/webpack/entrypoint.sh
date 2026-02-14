#!/bin/sh
set -e

# Create empty keys file if one does not already exist
if [ ! -f src/backend/web/static/javascript/tba_js/tba_keys.js ]; then
    cp src/backend/web/static/javascript/tba_js/tba_keys_template.js \
       src/backend/web/static/javascript/tba_js/tba_keys.js
fi

echo "Installing node dependencies..."
npm ci

# Build legacy concatenated JS bundles
uv run --group webpack python3 ./ops/build/do_compress.py

# Run webpack in watch mode (dev) or one-shot build (CI/deploy)
if [ "${WATCH}" = "true" ]; then
    # Watch legacy JS files for changes and recompress in the background
    uv run --group webpack python3 ./ops/build/do_compress.py --watch &
    echo "Starting webpack in watch mode..."
    npm run dev
else
    echo "Running production webpack build..."
    npm run build
fi

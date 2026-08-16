#!/bin/bash
set -euo pipefail

echo "Installing pwa node dependencies..."
# Without an explicit --store-dir, pnpm drops a store in the repo root because
# node_modules is on its own volume
pnpm install --frozen-lockfile --store-dir "${PNPM_STORE_DIR:-/pnpm/store}"

exec "$@"

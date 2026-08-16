#!/bin/bash
set -euo pipefail

echo "Installing node and pnpm..."
mise install

echo "Installing pwa node dependencies..."
# Without --store-dir pnpm drops a store in the repo root, since node_modules is a volume
mise exec -- pnpm install --frozen-lockfile --store-dir "${PNPM_STORE_DIR:-/pnpm/store}"

exec mise exec -- "$@"

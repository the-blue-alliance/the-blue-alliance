#!/bin/sh
set -e

# Check if data already exists
if [ ! -d "/data/auth_export" ]; then
  echo "Creating initial auth accounts..."
  firebase emulators:exec --project=$PROJECT_ID --export-on-exit=/data 'node create_auth_emulator_accounts.js'
fi

echo "Starting emulators with persisted data..."
firebase emulators:start --project=$PROJECT_ID --import=/data

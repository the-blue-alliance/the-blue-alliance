#!/bin/bash
set -eo pipefail

# source ops/dev/vagrant/config.sh

error_exit() {
    echo "$1" 1>&2
    exit 1
}

[[ -z "${FIREBASE_PROJECT}" ]] && error_exit "FIREBASE_PROJECT environment variable missing"

# Start Firebase emulators
emulator_cmd="firebase emulators:start --project=${FIREBASE_PROJECT}"
$emulator_cmd &
firebase_pid=$!

cleanup() {
    echo "Terminating background services..."
    if [[ -n "$firebase_pid" ]]; then
        kill -SIGTERM "$firebase_pid" || echo "Failed to terminate Firebase process"
        wait "$firebase_pid" 2>/dev/null
    fi
}

trap cleanup INT TERM SIGTERM SIGINT

wait

# Give the emualtor a second to boot before inserting users
# sleep 500

# python ops/dev/vagrant/create_auth_emulator_accounts.py --project="$project"

# fg

#!/bin/bash
set -e

source ops/dev/vagrant/config.sh

# We start the emulator regardless of whether we use the local or remote datastore
# It's just easier that way

# The project/port should match what's configured in the dev_appserver invocation
project=$(project)
emulator_port=8089
datastore_path="/datastore/tba.db"

gcloud beta emulators datastore start --project="$project" --data-dir="$datastore_path" --host-port="0.0.0.0:$emulator_port"

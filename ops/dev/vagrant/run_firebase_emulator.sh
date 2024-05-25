#!/bin/bash -i
set -e

source ops/dev/vagrant/config.sh

project=$(project)

firebase emulators:start --project="$project" &

# Give the emualtor a second to boot before inserting users
sleep 500

python ops/dev/vagrant/create_auth_emulator_accounts.py --project="$project"

fg

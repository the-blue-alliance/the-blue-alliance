#!/bin/bash -i
set -e

source ops/dev/vagrant/config.sh

project=$(project)

firebase emulators:exec --project="$project" --import=.firebase-data --export-on-exit=.firebase-data "python ops/dev/vagrant/create_auth_emulator_accounts.py --project='$project'"

firebase emulators:start --project="$project" --import=.firebase-data --export-on-exit=.firebase-data

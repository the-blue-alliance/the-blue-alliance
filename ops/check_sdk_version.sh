#! /bin/bash

source ops/dev/vagrant/config.sh

min_version=$(get_config_prop min_gcloud_sdk_version)

function help_on_error() {
    echo "Your dev container is running an outdated Google Cloud SDK!"
    echo "The Blue Alliance requires at least version ${min_version}"
    echo "Update your container by running: vagrant halt && vagrant up --provision"
}

set -eE
trap 'help_on_error' ERR

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "No venv detected, exiting..."
    exit 0
fi

python3 ops/check_sdk_version.py "$min_version"

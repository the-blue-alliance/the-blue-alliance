#! /bin/bash

function help_on_error() {
    echo "You have mismatched dependencies!"
    echo "Try running using a venv: https://github.com/the-blue-alliance/the-blue-alliance/wiki/Repo-Setup#virtualenv-install"
    echo "And make sure everything is up to date by running: pip install -r requirements.txt && pip install -r src/requirements.txt"
}

set -eE
trap 'help_on_error' ERR

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "No venv detected, exiting..."
    exit 0
fi

python3 ops/check_venv_deps.py

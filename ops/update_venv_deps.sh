#! /bin/bash
set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "No venv detected, exiting..."
    exit 0;
fi

pip install -r requirements.txt
pip install -r src/requirements.txt

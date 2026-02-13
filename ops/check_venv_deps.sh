#! /bin/bash

function help_on_error() {
    echo "Your dependencies are out of sync!"
    echo "Run 'uv sync --group dev' or 'make sync' to update."
}

set -eE
trap 'help_on_error' ERR

if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

uv sync --check --group dev

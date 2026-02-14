#! /bin/bash
set -e

if ! command -v uv &>/dev/null; then
    echo "uv is not installed, skipping dependency sync..."
    exit 0
fi

uv sync --group dev

#! /bin/bash

set -eE

if [[ ! -f "/usr/bin/docker" ]]; then
    echo "No docker install detected, exiting..."
    exit 0
fi

INITIAL_SHA=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" 2>&1 | grep "ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest" | awk '{print $2}')
docker pull --quiet ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest 1>/dev/null 2>/dev/null
FINAL_SHA=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" 2>&1 | grep "ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest" | awk '{print $2}')

if [[ "$INITIAL_SHA" != "$FINAL_SHA" ]]; then
    echo "Dev container updated. To recreate, run: vagrant halt && vagrant destroy && vagrant up"
fi

#! /bin/bash

CONTAINER_NAME="tba-py3"

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Found running container, pulling logs..."
else
    echo "Container not running, skipping..."
    exit 0
fi

docker cp "${CONTAINER_NAME}:/var/log/tba.log" "/tmp/tba.log"

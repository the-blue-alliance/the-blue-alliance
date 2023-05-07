#! /bin/bash

if vagrant status default | grep -q 'running'; then
    echo "Found running container to $1 datastore"
else
    echo "Vagrant container not running, skipping..."
    exit 0
fi

config=$(vagrant ssh-config)

host=$(echo -e "${config}" | grep HostName | cut -d " " -f 4)
port=$(echo -e "${config}" | grep Port | cut -d " " -f 4)
keyfile=$(echo -e "${config}" | grep IdentityFile | cut -d " " -f 4)

scp -P "$port" -i "$keyfile" -oStrictHostKeyChecking=no "root@$host:/var/log/tba.log" "/tmp/tba.log"

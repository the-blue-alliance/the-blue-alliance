#!/bin/bash

vagrant plugin install vagrant-gatling-rsync

sed -i 's/  # Forward GAE modules.*$/  if Vagrant.has_plugin?("vagrant-gatling-rsync") \
    config.gatling.latency = 2.5 \
    config.gatling.time_format = "%H:%M:%S" \
  end \
  config.gatling.rsync_on_startup = false \
\n&/' Vagrantfile

sed -i 's/rsync-auto/gatling-rsync-auto/' ops/dev/host.sh


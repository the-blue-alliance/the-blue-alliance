# -*- mode: ruby -*-
# vi: set ft=ruby:expandtab:tabstop=2:softtabstop=2

Vagrant.configure("2") do |config|

  # Sync the TBA code directory
  config.vm.synced_folder "./", "/tba",
    type: "rsync",
    owner: "root",
    group: "root",
    rsync__rsync_path: "rsync",
    rsync__exclude: [
      ".git/"
    ],
    rsync__auto: true

  # Forward GAE modules
  ports = []
  for i in 8080..8089
    ports.push("#{i}:#{i}")
    config.vm.network "forwarded_port", guest: i, host: i
  end

  # Forward GAE admin
  ports.push("8000:8000")
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # Provision with docker
  config.vm.hostname = "tba-docker"
  config.vm.provider "docker" do |d|
    d.build_dir = "ops/dev"
    d.ports = ports
    d.has_ssh = true
  end

  # Configure ssh into container
  config.ssh.insert_key = true
  config.ssh.username = "root"
  config.ssh.password = "tba"
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"

  # Provision dependencies
  config.vm.provision "shell",
    inline: "cd /tba && ./ops/dev/bootstrap-dev-container.sh",
    privileged: false
 
  # Start the GAE devserver
  config.vm.provision "shell",
    inline: "cd /tba && ./ops/dev/start-devserver.sh",
    privileged: false,
    run: "always"
end

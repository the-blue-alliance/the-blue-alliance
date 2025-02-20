# -*- mode: ruby -*-
# vi: set ft=ruby:expandtab:tabstop=2:softtabstop=2

Vagrant.require_version "> 2.1.0"
Vagrant.configure("2") do |config|

  # Sync the TBA code directory
  config.vm.synced_folder "./", "/tba",
    type: "rsync",
    owner: "root",
    group: "root",
    rsync__rsync_path: "rsync",
    rsync__exclude: [
      ".git/",
      "node_modules/",
      "src/build/*",
      "__pycache__",
      "venv/*",
      ".pyre/*",
    ],
    rsync__auto: true

  ports = []

  # Forward Firebase ports
  for i in [4000, 4400, 4500, 9005, 9000, 9099]
    ports.push("#{i}:#{i}")
    config.vm.network "forwarded_port", guest: i, host: i
  end

  # Forward GAE modules
  # Only forward 8080 on CI since some others conflict with GH Actions
  # and are not needed for testing.
  if ENV['CI'] != nil
    gae_module_ports = [8080]
  else
    gae_module_ports = 8080..8089
  end

  for i in gae_module_ports
    ports.push("#{i}:#{i}")
    config.vm.network "forwarded_port", guest: i, host: i
  end

  # Forward GAE admin
  ports.push("8000:8000")
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # Forward RQ Dashboard
  ports.push("9181:9181")
  config.vm.network "forwarded_port", guest: 9181, host: 9181

  # Provision with docker
  config.vm.hostname = "tba-py3-docker"
  config.vm.provider "docker" do |d|
    d.name = "tba-py3"
    d.ports = ports
    d.has_ssh = true

    if ENV['CI'] != nil
      # On CI, we use the locally prebuilt image
      d.image = "localhost:5000/tba-py3-dev:latest"
    else
      if ENV['TBA_LOCAL_DOCKERFILE'] != nil
        # We can build the docker container from the local Dockerfile
        d.build_dir = "ops/dev/docker"
      else
        # But by deafult, run with a prebuilt container image because it's faster
        d.image = "ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest"
      end
    end


  end

  # Configure ssh into container
  config.ssh.insert_key = true
  config.ssh.username = "root"
  config.ssh.password = "tba"
  config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"

  # Provision dependencies
  config.vm.provision "shell",
    inline: "cd /tba && ./ops/dev/vagrant/bootstrap-dev-container.sh",
    privileged: false

  # Load in the datastore file, needs to run before devserver start
  #config.vm.provision "shell",
  #  inline: "cd /tba && ./ops/dev/pull-datastore.sh push",
  #  privileged: false

  # Start the GAE devserver
  config.vm.provision "shell",
    inline: "cd /tba && ./ops/dev/vagrant/start-devserver.sh",
    privileged: false,
    run: "always"

  # When the container halts, pull the datastore files
  #config.trigger.before [:halt, :destroy] do |trigger|
  #  trigger.info = "Pulling datastore from remote container"
  #  trigger.run = {inline: "./ops/dev/pull-datastore.sh pull"}
  #end

  # Fix for WSL
  # Source: https://github.com/hashicorp/vagrant/issues/10576
  config.vm.synced_folder '.', '/vagrant', disabled: true
end

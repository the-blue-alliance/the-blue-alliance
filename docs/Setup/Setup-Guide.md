# Setup Guide
## Install Tools
Local development for The Blue Alliance uses a [Vagrant](https://www.vagrantup.com/) + [Docker](https://www.docker.com/) container setup. This allows for isolation of all dependencies and tools required to run The Blue Alliance locally to be installed in a self-contained instance.

1. Install [Vagrant](https://www.vagrantup.com/downloads)
2. Install [Docker](https://docs.docker.com/get-docker/)
	* Windows Home users will need install the WSL. Follow the [Windows Home](https://docs.docker.com/docker-for-windows/install-windows-home/) installation instructions for more details.

## Fork/Clone
This section assumes a minimal setup and knowledge of Git/GitHub. For those that are unfamiliar with either, see the [Getting started with GitHub](https://help.github.com/en/github/getting-started-with-github) guide and the [Git Handbook](https://guides.github.com/introduction/git-handbook/)

[clone](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) the project, optionally from your own [fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) of [`the-blue-alliance/the-blue-alliance`](https://github.com/the-blue-alliance/the-blue-alliance) if you plan to submit a pull request to The Blue Alliance.

## Starting the Container
Before starting the container, ensure that Vagrant and Docker are both up and running.
```
$ vagrant up
```

After a little bit of installation and setup, a local instance of The Blue Alliance will be accessible at [localhost:8080](http://localhost:8080). The Google App Engine admin panel for the local instance can be access at [localhost:8000](http://localhost:8000).

## Working in the Container
### Automatically
The `ops/dev/host.sh` script will manage automatically syncing changes from your local environment to the container when files are changed, as well as surface the Google App Engine logs to the current terminal window.
```
$ ./ops/dev/host.sh
```

### Manually
To automatically sync changes from your local environment to the container, run `vagrant rsync-auto`. `vagrant rsync` can be used for a one-time manual sync if `vagrant rsync-auto` takes too long to detect/sync local changes.

Connect to the container via `vagrant ssh`. Process in the container run connected to a [tmux](https://github.com/tmux/tmux/wiki) session. You can connect to the `tmux` session via `tmux a`. The first tab is a `bash` session `cd`’d to the project’s working directory, `/tba`. The second tab is the [`dev_appserver.py`](https://cloud.google.com/appengine/docs/standard/python3/testing-and-deploying-your-app#local-dev-server) output which contains Google App Engine logs. Other `tmux` tabs are labeled based on the foregrounded process running.

```
# Sync changes in one tab
$ vagrant rsync-auto

# ssh in to dev container in one tab
$ vagrant ssh
> tmux attach
```

## What’s Next?
The [[development runbook|Development-Runbook]] has documentation for good next steps when working on The Blue Alliance, including bootstrapping data from production to your development environment. Before submitting a PR, make sure to run the [[tests, lints, and type checks|Test-Lint-Check]] locally.

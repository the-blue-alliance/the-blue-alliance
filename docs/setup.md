# Setup

## Install Tools
Local development for The Blue Alliance uses a [Vagrant](https://www.vagrantup.com/) + [Docker](https://www.docker.com/) container setup. This allows for isolation of all dependencies and tools required to run The Blue Alliance locally to be installed in a self-contained instance.

1. Install [Vagrant](https://www.vagrantup.com/downloads)
2. Install [Docker](https://docs.docker.com/get-docker/)
	* Windows Home users will need install the WSL. Follow the [Windows Home](https://docs.docker.com/docker-for-windows/install-windows-home/) installation instructions for more details.

## Fork/Clone
This section assumes a minimal setup and knowledge of Git/GitHub. For those that are unfamiliar with either, see the [Getting started with GitHub](https://help.github.com/en/github/getting-started-with-github) guide and the [Git Handbook](https://guides.github.com/introduction/git-handbook/)

[fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) the [`the-blue-alliance/the-blue-alliance`](https://github.com/the-blue-alliance/the-blue-alliance) and [clone](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) the code.

## Starting the Container
Before starting the container, ensure that Vagrant and Docker are both up and running.

1. Ensure Vagrant is running
2. Ensure Docker is running
	* On Linux, `sudo service docker start`
	* On Mac/Windows, launch the Docker Desktop app
3. Start the container
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

## Repo Setup (Optional)
A small amount of repo configuration can be done in order to streamline development. This step is optional as it is not required for working in The Blue Alliance repo, but it will be helpful for contributors that plan to do frequent work in the repo. This setup happens in your local environment, not in the development container.

### Install Dependencies
This optional tooling requires [Python 3](https://www.python.org/downloads/) and [`pip`](https://pip.pypa.io/en/stable/installing/) to install.

1. Install [Python 3](https://www.python.org/downloads/)
2. Install [`pip`](https://pip.pypa.io/en/stable/installing/)

If you have both a Python 2 and Python 3 interpreter on your machine, run the `pip3` command instead of `pip`. To confirm, run -
```
$ ls -l `which pip`
```
If the path is a `2.7(.X)` path, run `pip3` instead of `pip`. If the path is a `3.7(.X)` path, run `pip`.

#### Globally Install
```
$ pip install -r requirements.txt
```

#### virtualenv install
[virtaulenv](https://virtualenv.pypa.io/en/latest/) can be used to keep these Python dependencies local to The Blue Alliance project.
```
$ pip install virtaulenv
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Pre-Commit Hook
Install the pre-commit hook to automatically run a series of checks before committing your code upstream. This will ensure that basic issues (linting, type checking, etc.) are fixed locally happen before committing your code upstream.
```
$ pre-commit install
```
In the case that you want to bypass the pre-commit hook when committing code, you can commit using the `—no-verify` flag
```
$ git commit -m "Bypasing pre-commit hook" --no-verify
```

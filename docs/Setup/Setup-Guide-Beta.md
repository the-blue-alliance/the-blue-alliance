## Install Tools
Local development for The Blue Alliance uses a [Docker](https://www.docker.com/) container setup. This allows for isolation of all dependencies and tools required to run The Blue Alliance locally to be installed in a self-contained instance.

1. Install [Docker](https://docs.docker.com/get-docker/)

## Fork/Clone
This section assumes a minimal setup and knowledge of Git/GitHub. For those that are unfamiliar with either, see the [Getting started with GitHub](https://help.github.com/en/github/getting-started-with-github) guide and the [Git Handbook](https://guides.github.com/introduction/git-handbook/)

[Clone](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) the project, optionally from your own [fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) of [`the-blue-alliance/the-blue-alliance`](https://github.com/the-blue-alliance/the-blue-alliance) if you plan to submit a pull request to The Blue Alliance.

## Starting the Container
Before starting the container, ensure that Docker is up and running.
```
$ docker-compose up
```

After a little bit of installation and setup, a local instance of The Blue Alliance will be accessible at [localhost:8080](http://localhost:8080). The Google App Engine admin panel for the local instance can be access at [localhost:8000](http://localhost:8000).

## Working in the Container
### Automatically

`docker-compose` will automatically manage syncing changes from your local environment to the container when files are changed, added, or removed. This means that you can use your favorite editor or IDE to edit files locally and the changes will automatically be reflected in the container in real time.

### Manually

You can connect to the container via `docker-compose exec tba bash`. Processes in the container run connected to a [tmux](https://github.com/tmux/tmux/wiki) session. You can connect to the `tmux` session via `tmux a`. The first tab is a `bash` session `cd`’d to the project’s working directory, `/tba`. The second tab is the [`dev_appserver.py`](https://cloud.google.com/appengine/docs/standard/python3/testing-and-deploying-your-app#local-dev-server) output which contains Google App Engine logs. Other `tmux` tabs are labeled based on the foregrounded process running.

```
# ssh in to dev container in one tab
$ docker-compose exec tba bash
> tmux attach
```

## What’s Next?
The [[development runbook|Development-Runbook]] has documentation for good next steps when working on The Blue Alliance, including bootstrapping data from production to your development environment. Before submitting a PR, make sure to run the [[tests, lints, and type checks|Test-Lint-Check]] locally.

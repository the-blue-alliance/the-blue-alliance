## Install Tools
Local development for The Blue Alliance requires two tools:

1. **[Docker](https://docs.docker.com/get-docker/)** — for running the local dev server (App Engine emulator, Datastore, Firebase, webpack)
2. **[uv](https://docs.astral.sh/uv/)** — for managing Python dependencies and running tests/linting

### Install Docker
Install [Docker](https://docs.docker.com/get-docker/) for your platform.

### Install uv
Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

`uv` will automatically download the correct Python version (from `.python-version`) and manage a virtual environment for you. You do **not** need to install Python separately.

## Fork/Clone
This section assumes a minimal setup and knowledge of Git/GitHub. For those that are unfamiliar with either, see the [Getting started with GitHub](https://help.github.com/en/github/getting-started-with-github) guide and the [Git Handbook](https://guides.github.com/introduction/git-handbook/)

[Clone](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) the project, optionally from your own [fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) of [`the-blue-alliance/the-blue-alliance`](https://github.com/the-blue-alliance/the-blue-alliance) if you plan to submit a pull request to The Blue Alliance.

## Starting the Dev Environment
Before starting the containers, ensure Docker is running. Then start all services:

```
$ docker-compose up --build
```

**Note:** Always use `--build` so Docker picks up any Dockerfile changes. This is fast when nothing has changed due to layer caching. The container automatically generates `src/requirements.txt` on startup, so there is no need to run `make freeze` manually.

After a little bit of installation and setup, a local instance of The Blue Alliance will be accessible at [localhost:8080](http://localhost:8080). The Google App Engine admin panel for the local instance can be accessed at [localhost:8000](http://localhost:8000).

### Services

`docker-compose` runs four services:

| Service | Description | Ports |
| --- | --- | --- |
| `tba` | GAE dev_appserver (Python backend) | 8000 (admin), 8080-8088 (modules) |
| `webpack` | Watches and rebuilds JS/CSS on file changes | — |
| `datastore` | Cloud Datastore emulator | 8089 |
| `firebase` | Firebase Auth + Realtime DB emulators | 4000, 9000, 9099 |

## Working with the Dev Environment

### Live Reloading

Changes are automatically synced to all containers via Docker bind mounts. When you edit code locally:
- **Python changes**: `dev_appserver.py` detects changes and reloads automatically
- **JS/CSS changes**: The `webpack` service watches for changes and rebuilds automatically

### Viewing Logs

Each service outputs its own logs. Use `docker-compose logs` to view them:

```bash
# Follow all service logs
$ docker-compose logs -f

# Follow logs for a specific service
$ docker-compose logs -f tba
$ docker-compose logs -f webpack
```

### Shell Access

You can open a shell inside the `tba` container:

```bash
$ docker-compose exec tba bash
```

### Stopping

```bash
# Stop all services
$ docker-compose down

# Stop and remove volumes (resets datastore data)
$ docker-compose down --volumes
```

## Running Tests, Linting, and Type Checks

Tests, linting, and type checking run on the **host** via `uv` (not inside Docker). Dependencies are synced automatically — there is no need to run `make sync` first. See the [[test, lint, and type check documentation|Test-Lint-Check]] for details.

```bash
# Run all tests
$ make test

# Run linter
$ make lint

# Run type checker
$ make typecheck
```

## What's Next?
The [[development runbook|Development-Runbook]] has documentation for good next steps when working on The Blue Alliance, including bootstrapping data from production to your development environment. Before submitting a PR, make sure to run the [[tests, lints, and type checks|Test-Lint-Check]] locally.

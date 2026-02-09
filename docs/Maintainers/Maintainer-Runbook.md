## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow these steps:

1. Update the version in `.python-version`
2. Run `./ops/check_python_version.sh --update` to update all dependent files:
   - GAE service `.yaml` files (`runtime:` directive)
   - `docker-compose.yml` (`x-python-version:`)
   - Dockerfiles (`ARG PYTHON_VERSION=`)
   - GitHub Actions workflow files (`python-version:`)
3. Verify the changes: `./ops/check_python_version.sh`
4. Update the [[Repo Setup|Repo-Setup]] docs if they reference a specific Python version

## Building a New Development Container Version

We host built container images with [GitHub Container Registry](https://github.com/features/packages). The `Dockerfile` is defined [here](https://github.com/the-blue-alliance/the-blue-alliance/tree/main/ops/dev/docker). After the `Dockerfile` is updated, we'll need to trigger a rebuild + push by including `[dockerpublish]` in the commit message.

Images are published to `ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest` and can be managed from the [on GitHub](https://github.com/the-blue-alliance/the-blue-alliance/pkgs/container/the-blue-alliance%2Ftba-py3-dev).

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.**

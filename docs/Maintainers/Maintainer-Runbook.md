## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow the following steps to bump the Python version -

1) Update the [`runtime` directive in the service `.yaml` files](https://cloud.google.com/appengine/docs/standard/python3/config/appref)
2) Update the [`python-version`](https://docs.github.com/en/actions/guides/building-and-testing-python#specifying-a-python-version) in the GitHub Actions (`.github/workflows/*.yml`) files
3) Update the [[Repo Setup|Repo-Setup]] docs to reflect the new Python version


## Building a New Development Container Version

We host built container images with [GitHub Container Registry](https://github.com/features/packages). The `Dockerfile` is defined [here](https://github.com/the-blue-alliance/the-blue-alliance/tree/py3/ops/dev/docker). After the `Dockerfile` is updated, we'll need to trigger a rebuild + push by including `[dockerpublish]` in the commit message.

Images are published to `ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest` and can be managed from the [on GitHub](https://github.com/the-blue-alliance/the-blue-alliance/pkgs/container/the-blue-alliance%2Ftba-py3-dev).

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.** After modifying the database, be sure to clear the Redis cache to remove any stale cached data.

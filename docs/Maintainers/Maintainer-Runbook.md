## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow the following steps to bump the Python version -

1) Update the [`runtime` directive in the service `.yaml` files](https://cloud.google.com/appengine/docs/standard/python3/config/appref)
2) Update the [`python-version`](https://docs.github.com/en/actions/guides/building-and-testing-python#specifying-a-python-version) in the GitHub Actions (`.github/workflows/*.yml`) files
3) Update the [[Repo Setup|Repo-Setup]] docs to reflect the new Python version


## Building a New Development Container Version

We host built container images with [Google Cloud Build](https://cloud.google.com/cloud-build). The build config and `Dockerfile` are [in the repo](https://github.com/the-blue-alliance/the-blue-alliance/tree/py3/ops/dev/docker). After the `Dockerfile` is updated, we'll need to rebuild + push the image:

```bash
# Locally, you need gcloud and docker installed
$ ./ops/dev/docker/build-container-images.sh
```

Images are published to `gcr.io/tbatv-prod-hrd/tba-py3-dev` and can be managed from the [cloud console](https://console.cloud.google.com/gcr).

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.** After modifying the database, be sure to clear the Redis cache to remove any stale cached data.

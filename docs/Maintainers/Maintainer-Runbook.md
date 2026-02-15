## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow these steps:

1. Update the version in `.python-version`
2. Run `./ops/check_python_version.sh --update` to update all dependent files:
   - `pyproject.toml` (`requires-python`)
   - GAE service `.yaml` files (`runtime:` directive)
3. Verify the changes: `./ops/check_python_version.sh`

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.**

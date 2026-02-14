Tests and linting run via `make` commands, which use [`uv`](https://docs.astral.sh/uv/) to manage a local virtualenv. Dependencies are synced automatically on first run — just run `make test` or `make lint` and everything bootstraps itself.

If you want to sync all dev dependencies explicitly (test + lint + typecheck + pre-commit):

```bash
$ make sync
```

# Python

## Tests

```bash
# Run all tests
$ make test

# Run a specific test file
$ make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'

# Run a specific test class
$ make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'

# Run a specific test method
$ make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper::test_ping_webhook'

# Run tests matching a name pattern
$ make test ARGS='src/ -k "test_ping"'
```

## Lint

```bash
# Run linter (black --check + flake8)
$ make lint

# Auto-fix formatting with black, then run flake8
$ make lint ARGS='--fix'
```

## Type Checker

The Blue Alliance's Python codebase enforces the use of [type hints](https://www.python.org/dev/peps/pep-0484/) using [pyre](https://pyre-check.org/).

```bash
$ make typecheck
```

#### Generating Type Checker Stubs

The `stubs/` folder contains [type hint stubs](https://www.python.org/dev/peps/pep-0484/#stub-files) for third-party dependencies that do not natively contain type hints. These type hints are necessary for [pyre](https://pyre-check.org/) (our type checker) to run successfully.

Before generating stubs, check to see if type hints are exposed for a library via it's `site-packages` directory by adding the library in question to the [pyre search paths in our .pyre_configuration](https://github.com/the-blue-alliance/the-blue-alliance/blob/main/.pyre_configuration). This is a preferred solution to generating stubs. If the typecheck run still fails, generating stubs is an appropriate solution.

In order to generate stubs for a third-party library, run [`stubgen`](https://mypy.readthedocs.io/en/stable/stubgen.html) for the third-party package. For For example, to generate stubs for the `google.cloud.ndb` library -

```
$ stubgen -p google.cloud.ndb -o stubs/
```

#### Patching Type Checker Stubs

`stubgen` stubs our type checker but doesn’t add proper types. Manual edits to the type checking stubs can be made. Any edits should be checked in to source control as a patch file so they may be re-applied easily if dependencies are updated and stubs need to be re-generated. `mypy` must be installed for `stubgen`

```
$ pip install mypy
```

To create a patch file, first make changes to the stubs and then save the differences to a patch file.

```
$ git diff > stubs/patch/{module}.patch
```

Changes can then be applied via `git patch`. After generating new stubs for a library, be sure to apply all existing patches.

```
$ git apply stubs/patch/*.patch
```

# Node

## Tests

Node tests are run using [Jest](https://jestjs.io/).

```bash
> ./ops/test_node.sh
```

## Lint

Node linting runs using [ESLint](https://eslint.org/). Run using the `ops/lint_node.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.

```bash
# Check for linter errors
> ./ops/lint_node.sh
# Fixing linter errors automatically
> ./ops/lint_node.sh --fix
```

# Bash

## Lint

Bash linting runs [shellcheck](https://www.shellcheck.net/) for static analysis and [shfmt](https://github.com/mvdan/sh) for formatting.

```bash
# Run bash linter (shellcheck + shfmt)
$ make lint-bash

# Auto-fix formatting with shfmt
$ make lint-bash ARGS='--fix'
```

# Python Version Consistency

The project maintains consistent Python versions across all configuration files (GAE yamls, Docker configs, CI workflows). Use the provided script to check or update versions:

```bash
# Check Python version consistency
$ ./ops/check_python_version.sh

# Update all files to match .python-version
$ ./ops/check_python_version.sh --update
```

The source of truth for the Python version is the `.python-version` file in the repository root.

The documentation for running tests, lints, and checks assumes that dependencies have been installed in a local environment outside of the development container. See the [[Repo Setup|Repo-Setup]] page for details. Tests and type checks can be run either in the development container or in your local environment. Lints are recommended to be run in your local environment since Vagrant will not sync fixes done automatically by the linter (the `--fix` option) in the container back out to your local environment.

## Python

### Tests

Python tests are run using [pytest](https://docs.pytest.org/en/latest/). You can specify a single file to test, or a directory to run all downstream tests (`test_*.py` files) for. The `--relevant` flag can be used to only test modified codepaths.

```bash
# Run all tests in src/ folder
> pytest src/

# Run only tests for downstream code changes in the src/ folder
> pytest src/ --relevant
```

### Lint

Python linting is a two-step process - running [`black`](https://black.readthedocs.io/en/stable/) and [`flake8`](https://flake8.pycqa.org/en/latest/). Run them together with the `lint_py3.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.

```bash
# Check for linter errors
> ./ops/lint_py3.sh

# Fixing linter errors automatically
> ./ops/lint_py3.sh --fix
```

### Type Checker

The Blue Alliance's Python codebases enforces the use of [type hints](https://www.python.org/dev/peps/pep-0484/) using [pyre](https://pyre-check.org/).

```bash
> ./ops/typecheck_py3.sh
```

By default, `pyre` will attempt to spin up `watchman` to speed up subsequent `pyre` runs. This behavior can be avoided by using `pyre check`.

```bash
> pyre check
```

#### Generating Type Checker Stubs

The `stubs/` folder contains [type hint stubs](https://www.python.org/dev/peps/pep-0484/#stub-files) for third-party dependencies that do not natively contain type hints. These type hints are necessary for [pyre](https://pyre-check.org/) (our type checker) to run successfully.

Before generating stubs, check to see if type hints are exposed for a library via it's `site-packages` directory by adding the library in question to the [pyre search paths in our .pyre_configuration](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/.pyre_configuration). This is a preferred solution to generating stubs. If the typecheck run still fails, generating stubs is an appropriate solution.

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

Changes can then be applied via `git patch`.  After generating new stubs for a library, be sure to apply all existing patches.
```
$ git apply stubs/patch/*.patch
```

## Node

### Tests

Node tests are run using [Jest](https://jestjs.io/).

```bash
> ./ops/test_node.sh
```

### Lint

Node linting runs using [ESLint](https://eslint.org/). Run using the `ops/lint_node.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.

```bash
# Check for linter errors
> ./ops/lint_node.sh
# Fixing linter errors automatically
> ./ops/lint_node.sh --fix
```

## Bash

### Lint

Formatting bash requires [shfmt](https://github.com/mvdan/sh) to be install on the local system. Run using the `ops/lint_bash.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style.

```bash
# Check for errors
> ./ops_lint_bash.sh
# Fix formatting errors automatically
> ./ops_lint_bash.sh --fix
```

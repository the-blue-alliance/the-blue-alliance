# Development Runbook

## Bootstrapping Data

(TODO: Update for Python 3)

## Rebuilding Web Resources (JavaScript, CSS, etc.)
If you make changes to JavaScript or CSS files for the `web` service, you will have to recompile the files in order for the changes to show up in your browser. After syncing changes from your local environment to the development container, run the `ops/build/run_buildweb.sh.sh` script from inside the development container.

## Running Tests/Lint/etc.

### Running Tests (Python)
Python tests are run using [pytest](https://docs.pytest.org/en/latest/). You can specify a single file to test, or a directory to run all downstream tests (`test_*.py` files) for. The `--relevant` flag can be used to only test modified codepaths.
```
# Run all tests in src/ folder
$ pytest src/
# Run only tests for downstream code changes in the src/ folder
$ pytest src/ --relevant
```

### Running Lint (Python)
Python linting is a two-step process - running [`black`](https://black.readthedocs.io/en/stable/) and [`flake8`](https://flake8.pycqa.org/en/latest/). Run them together with the `ops/lint_py3.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.
```
# Check for linter errors
$ ./ops/lint_py3.sh
# Fixing linter errors automatically
$ ./ops/lint_py3.sh --fix
```

### Running Type Checker (Python)
The Blue Alliance's Python codebases enforces the use of [type hints](https://www.python.org/dev/peps/pep-0484/) using [pyre](https://pyre-check.org/).
```
$ ./ops/typecheck_py3.sh
```

### Running Tests (Node)
Node tests are run using [Jest](https://jestjs.io/).
```
$ ./ops/test_node.sh
```

### Running Lint (Node)
Node linting runs using [ESLint](https://eslint.org/). Run using the `ops/lint_node.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.
```
# Check for linter errors
$ ./ops/lint_node.sh
# Fixing linter errors automatically
$ ./ops/lint_node.sh --fix
```

## Using the local Dockerfile
By default Vagrant will look for the pre-built Docker container upstream when provisioning a development container. To use the local `Dockerfile`, comment out the [`d.image =`](https://github.com/the-blue-alliance/the-blue-alliance/blob/181043acc9759dd8347b89337d9f724451d8297f/Vagrantfile#L40) line and uncomment the [`d.build_dir =`](https://github.com/the-blue-alliance/the-blue-alliance/blob/181043acc9759dd8347b89337d9f724451d8297f/Vagrantfile#L43) line in the `Vagrantfile`.

## Reprovisioning the Development Container
If you run into issues, especially after not working with your dev instance for a while, try reprovisioning and restarting your development container.
```
$ vagrant up --provision
```

The Vagrant container may be out of date as well. In this situation, destroy and recreate your local Vagrant image.
```
$ vagrant halt
$ vagrant destroy
$ vagrant up
```

If you have problems destroying your container via Vagrant, you can remove the container via Docker.
```
$ docker stop tba
$ docker rm tba
$ vagrant up
```

## Generating Type Checker Stubs
The `stubs/` folder contains [type hint stubs](https://www.python.org/dev/peps/pep-0484/#stub-files) for third-party dependencies that do not natively contain type hints. These type hints are necessary for [pyre](https://pyre-check.org/) (our type checker) to run successfully. In order to generate stubs for a third-party library, run [`stubgen`](https://mypy.readthedocs.io/en/stable/stubgen.html) for the third-party package. For For example, to generate stubs for the `google.cloud.ndb` library -
```
$ stubgen -p google.cloud.ndb -o stubs/
```

### Patching Type Checker Stubs
`stubgen` stubs our type checker but doesn’t add proper types. Manual edits to the type checking stubs can be made. Any edits should be checked in to source control as a patch file so they may be re-applied easily if dependencies are updated and stubs need to be re-generated. To create a patch file, first make changes to the stubs and then save the differences to a patch file.
```
$ git diff > stubs/patch/{module}.patch
```

Changes can then be applied via `git patch`.  After generating new stubs for a library, be sure to apply all existing patches.
```
$ git apply stubs/patch/*.patch
```

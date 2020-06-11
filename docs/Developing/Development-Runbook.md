# Development Runbook

## Starting the Dev Environment

We recommend running a local version of The Blue Alliance inside a [docker](https://www.docker.com/) container. You can use [vagrant](https://www.vagrantup.com/) to provision the entire environment.

Local Dependencies:
 - [python3](https://wiki.python.org/moin/BeginnersGuide/Download)
 - [docker](https://www.docker.com/)
 - [vagrant](https://www.vagrantup.com/)

You can start the container locally by running `vagrant up`. Once the setup is complete, TBA should be accessable in a web browser at `localhost:8080`.

Once the container is running, you can print all the relevant logs (including the `dev_appserver` logs) on the host machine by running `./ops/dev/host.sh`.

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

The Vagrant container may be out of date as well. In this situation, destroy and recreate your local Vagrant image. You should also be sure you have the most up to date base container image.
```
$ vagrant halt
$ vagrant destroy
$ docker pull gcr.io/tbatv-prod-hrd/tba-py3-dev:latest
$ vagrant up
```

If you have problems destroying your container via Vagrant, you can remove the container via Docker.
```
$ docker stop tba
$ docker rm tba
$ vagrant up
```

## Configuring the Development Environment

It is possible to change the way the local instance inside the dev container runs using a local configuration file. The defaults are checked into the repo as `tba_dev_config.json` and should be sufficient for most everyday use. However, if you want to configure overrides locally, add a json file to `tba_dev_config.local.json` (which will be ignored by `git`). Note that you need to `halt` and restart the development container for changes to take effect.

Available configuration keys:
 - `datastore_mode` can be either `local` or `remote`. By default this is set to `local` and will use the [datastore emulator](https://cloud.google.com/datastore/docs/tools/datastore-emulator) bundled with the App Engine SDK. If instead, you want to point your instance to a real datatsore instance, set this to `remote` and also set the `google_application_credentials` property
 - `google_application_credentials` is a path (relative to the repository root) to a [service account JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) used to authenticate to a production Google Cloud service. We recommend to put these in `ops/dev/keys` (which will be ignored by `git`). Example: `ops/dev/keys/tba-prod-key.json`
 - `log_level`: This will be used to set the `--log-level` flag when invoking `dev_appserver`. See the [documentation](https://cloud.google.com/appengine/docs/standard/python3/tools/local-devserver-command) for allowed values.

## Generating Type Checker Stubs
The `stubs/` folder contains [type hint stubs](https://www.python.org/dev/peps/pep-0484/#stub-files) for third-party dependencies that do not natively contain type hints. These type hints are necessary for [pyre](https://pyre-check.org/) (our type checker) to run successfully. In order to generate stubs for a third-party library, run [`stubgen`](https://mypy.readthedocs.io/en/stable/stubgen.html) for the third-party package. For For example, to generate stubs for the `google.cloud.ndb` library -
```
$ stubgen -p google.cloud.ndb -o stubs/
```

### Patching Type Checker Stubs
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

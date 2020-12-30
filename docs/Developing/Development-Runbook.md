## Starting the Dev Environment

We recommend running a local version of The Blue Alliance inside a [docker](https://www.docker.com/) container. You can use [vagrant](https://www.vagrantup.com/) to provision the entire environment.

Local Dependencies:
 - [python3](https://wiki.python.org/moin/BeginnersGuide/Download)
 - [docker](https://www.docker.com/)
 - [vagrant](https://www.vagrantup.com/)

You can start the container locally by running `vagrant up`. Once the setup is complete, TBA should be accessable in a web browser at `localhost:8080`.

```
$ vagrant up
# http://localhost:8080
```

Once the container is running, you can automatically sync changes and the `dev_appserver` + Gulp logs on the host machine by running the `host.sh` script.

```
$ ./ops/dev/host.sh
# rsync-auto will start, logs will start streaming
```

## Bootstrapping Data

There are two ways to import data into a local development environment. You can either bootstrap the local db from the production site, or run the datafeeds locally to fetch data directly from FIRST.

### Bootstrapping from Prod TBA

When running locally, TBA will export a bootstrap interface at [http://localhost:8080/local/bootstrap](http://localhost:8080/local/bootstrap). You need to have an API key for the Read APIv3 on prod, which you can obtain on [your account page](https://www.thebluealliance.com/account). Then, you can choose which data you want to import by inputting its data key.

### Bootstrapping from FIRST

(TODO not implemented yet)

## Setup Javascript Secrets

Components in `web` (GameDay, login, etc.) make calls to Firebase and need to have Firebase keys set in order to work properly. Keys are referenced from a `tba_keys.js` file. This file is not checked in to source control, but an template of the file is. You can copy the template and add your own keys to the file.

```
$ cp src/backend/web/static/javascript/tba_js/tba_keys_template.js src/backend/web/static/javascript/tba_js/tba_keys.js
```

Edit the fields specified in the file and save. If you're using the development container, make sure to sync this file to the container. Finally, [rebuild web resources](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Development-Runbook#rebuilding-web-resources-javascript-css-etc) to compile the secrets file with the Javascript.

## Rebuilding Web Resources (JavaScript, CSS, etc.)

If you make changes to JavaScript or CSS files for the `web` service, you will have to recompile the files in order for the changes to show up in your browser. After syncing changes from your local environment to the development container, run the `run_buildweb.sh.sh` script from inside the development container.

```
$ ./ops/build/run_buildweb.sh.sh
```

## Running Tests/Typecheck/Lint/etc.

### Running Tests (Python)
Python tests are run using [pytest](https://docs.pytest.org/en/latest/). You can specify a single file to test, or a directory to run all downstream tests (`test_*.py` files) for. The `--relevant` flag can be used to only test modified codepaths.
```
# Run all tests in src/ folder
$ pytest src/
# Run only tests for downstream code changes in the src/ folder
$ pytest src/ --relevant
```

### Running Lint (Python)
Python linting is a two-step process - running [`black`](https://black.readthedocs.io/en/stable/) and [`flake8`](https://flake8.pycqa.org/en/latest/). Run them together with the `lint_py3.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.
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

### Running Typechecker/Lint/Tests Locally (outside of container)

In order to run the typechecker, tests, and lints outside of the dev container, you'll need to set up a [venv](https://docs.python.org/3/tutorial/venv.html). You can do so with the following commands:

```
# Create a venv
$ python3 -m venv ./venv

# Activate it
$ source ./venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt; pip install -r src/requirements.txt
```

The commands to run the typechecker, tests, and lints will be the same commands listed above.

## Using the local Dockerfile
By default Vagrant will look for the pre-built Docker container upstream when provisioning a development container. To use the local `Dockerfile`, set `TBA_LOCAL_DOCKERFILE` to be `true` and start the container normally.

```
$ TBA_LOCAL_DOCKERFILE=true vagrant up
Bringing machine 'default' up with 'docker' provider...
==> default: Creating and configuring docker networks...
==> default: Building the container from a Dockerfile...
```

## Reprovisioning the Development Container
If you run into issues, especially after not working with your dev instance for a while, try re-provisioning and restarting your development container.

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
 - `tasks_mode` can be either `local` or `remote`. By default this is set to `local` and will use Redis + RQ locally to enqueue tasks. If instead, you want to point your instance to a real Google Cloud Tasks queue, follow the setup instructions in the [[Google Cloud Tasks + ngrok|Queues-and-defer]] setup section.
  - `redis_cache_url` is a way to configure the location of a redis cache used for caching datastore responses. This defaults to `redis://localhost:6739`, which is the address of redis running inside the dev container. To disable the global cache, set this property to an empty string.
 - `google_application_credentials` is a path (relative to the repository root) to a [service account JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) used to authenticate to a production Google Cloud service. We recommend to put these in `ops/dev/keys` (which will be ignored by `git`). Example: `ops/dev/keys/tba-prod-key.json`
 - `log_level`: This will be used to set the `--log-level` flag when invoking `dev_appserver`. See the [documentation](https://cloud.google.com/appengine/docs/standard/python3/tools/local-devserver-command) for allowed values.
 - `tba_log_level`: This is used to configure the minimum log level for logs emitted by the TBA application. Allowed values correspond to the possible [`logging` library levels](https://docs.python.org/2/library/logging.html#logging-levels).

## Generating Type Checker Stubs
The `stubs/` folder contains [type hint stubs](https://www.python.org/dev/peps/pep-0484/#stub-files) for third-party dependencies that do not natively contain type hints. These type hints are necessary for [pyre](https://pyre-check.org/) (our type checker) to run successfully.

Before generating stubs, check to see if type hints are exposed for a library via it's `site-packages` directory by adding the library in question to the [pyre search paths in our .pyre_configuration](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/.pyre_configuration). This is a preferred solution to generating stubs. If the typecheck run still fails, generating stubs is an appropriate solution.

In order to generate stubs for a third-party library, run [`stubgen`](https://mypy.readthedocs.io/en/stable/stubgen.html) for the third-party package. For For example, to generate stubs for the `google.cloud.ndb` library -

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

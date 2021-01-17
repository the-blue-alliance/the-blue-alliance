## Starting the Dev Environment

We recommend running a local version of The Blue Alliance inside a [docker](https://www.docker.com/) container. You can use [vagrant](https://www.vagrantup.com/) to provision the entire environment.

Local Dependencies:
 - [python3](https://wiki.python.org/moin/BeginnersGuide/Download)
 - [docker](https://www.docker.com/)
 - [vagrant](https://www.vagrantup.com/)
 - *(optionally)* [watchman](https://facebook.github.io/watchman/)

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

If you make changes to JavaScript or CSS files for the `web` service, you will have to recompile the files in order for the changes to show up in your browser. After syncing changes from your local environment to the development container, run the `run_buildweb.sh` script from inside the development container.

```
$ ./ops/build/run_buildweb.sh
```

## Running Tests/Typecheck/Lint/etc.

### Set up local venv

In order to run the typechecker, tests, and lints outside of the dev container, you'll need to set up a [venv](https://docs.python.org/3/tutorial/venv.html). You can do so with the following commands:

```bash
# Create a venv
$ python3 -m venv ./venv

# Activate it
$ source ./venv/bin/activate

# Install dependencies
$ pip install -r requirements.txt; pip install -r src/requirements.txt
```

In large projects, running the typechecker can be slow, as there is a lot of code to parse. `pyre` can be sped up if [`watchman`](https://facebook.github.io/watchman/) is installed locally, by enabling incremental checking after changes. Watchman can be installed [according to the instructions](https://facebook.github.io/watchman/docs/install.html), or via your operating system's package manager or from source:

```bash
# On MacOS via homebrew
$ brew install watchman

# On Ubuntu (https://packages.ubuntu.com/search?keywords=watchman)
$ sudo apt-get install watchman

# On Fedora (https://koji.fedoraproject.org/koji/packageinfo?packageID=32733)
$ sudo dnf install watchman
```

The commands to run the typechecker, tests, and lints are listed below

### Running Tests (Python)
Python tests are run using [pytest](https://docs.pytest.org/en/latest/). You can specify a single file to test, or a directory to run all downstream tests (`test_*.py` files) for. The `--relevant` flag can be used to only test modified codepaths.

```bash
# Run all tests in src/ folder
$ pytest src/

# Run only tests for downstream code changes in the src/ folder
$ pytest src/ --relevant
```

### Running Lint (Python)
Python linting is a two-step process - running [`black`](https://black.readthedocs.io/en/stable/) and [`flake8`](https://flake8.pycqa.org/en/latest/). Run them together with the `lint_py3.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.

```bash
# Check for linter errors
$ ./ops/lint_py3.sh

# Fixing linter errors automatically
$ ./ops/lint_py3.sh --fix
```

### Running Type Checker (Python)
The Blue Alliance's Python codebases enforces the use of [type hints](https://www.python.org/dev/peps/pep-0484/) using [pyre](https://pyre-check.org/).

```bash
$ ./ops/typecheck_py3.sh
```

### Running Tests (Node)
Node tests are run using [Jest](https://jestjs.io/).

```bash
$ ./ops/test_node.sh
```

### Running Lint (Node)
Node linting runs using [ESLint](https://eslint.org/). Run using the `ops/lint_node.sh` script. Using the `--fix` flag will automatically reformat code that doesn't meet the style guide requirements.

```bash
# Check for linter errors
$ ./ops/lint_node.sh
# Fixing linter errors automatically
$ ./ops/lint_node.sh --fix
```

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

It is possible to change the way the local instance inside the dev container runs using a local configuration file. See the [`tba_dev_config.json`](https://github.com/the-blue-alliance/the-blue-alliance/wiki/tba_dev_config) documentation for more details.

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

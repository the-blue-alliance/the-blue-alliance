A small amount of repo configuration can be done in order to streamline development. This step is optional as it is not required for working in The Blue Alliance repo, but it will be helpful for contributors that plan to do frequent work in the repo. This setup happens in your local environment, not in the development container.

## Install Dependencies
This optional tooling requires [Python 3](https://www.python.org/downloads/) and [`pip`](https://pip.pypa.io/en/stable/installing/) to install.

1. Install [Python 3](https://www.python.org/downloads/) (3.9+)
2. Install [`pip`](https://pip.pypa.io/en/stable/installing/)
3. *(optionally)* Install [watchman](https://facebook.github.io/watchman/)
4. *(optionally)* Install [shfmt](https://github.com/mvdan/sh)

If you have both a Python 2 and Python 3 interpreter on your machine, run the `pip3` command instead of `pip`. To confirm, run -
```
$ ls -l `which pip`
```
If the path is a `2.7(.X)` path, run `pip3` instead of `pip`. If the path is a `3.8(.X)` path, run `pip`.

### virtualenv install
[virtaulenv](https://virtualenv.pypa.io/en/latest/) can be used to keep these Python dependencies local to The Blue Alliance project.
```
$ pip install virtaulenv
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Globally Install
```
$ pip install -r requirements.txt
```

## Pyre + Watchman

In large projects, running [Pyre](https://pyre-check.org/) (our Python typechecker) can be slow, as there is a lot of code to parse. `pyre` can be sped up if [`watchman`](https://facebook.github.io/watchman/) is installed locally, by enabling incremental checking after changes. Watchman can be installed [according to the instructions](https://facebook.github.io/watchman/docs/install.html), or via your operating system's package manager or from source:

```bash
# On MacOS via homebrew
$ brew install watchman

# On Ubuntu (https://packages.ubuntu.com/search?keywords=watchman)
$ sudo apt-get install watchman

# On Fedora (https://koji.fedoraproject.org/koji/packageinfo?packageID=32733)
$ sudo dnf install watchman
```

## Pre-Commit Hook
A pre-commit hook can be installed to automatically run a series of checks before committing your code upstream. This will ensure that basic issues (linting, type checking, etc.) are fixed locally happen before committing your code upstream.

```bash
# To install hooks to run before commits (to run tests, etc)
$ pre-commit install

# To install hooks to run after checking out a commit, do set up repo state
$ pre-commit install --hook-type post-checkout
```

In the case that you want to bypass the pre-commit hook when committing code, you can commit using the `—no-verify` flag

```bash
$ git commit -m "Bypasing pre-commit hook" --no-verify
```

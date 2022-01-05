## Configuring the Development Environment

It is possible to change the way the local instance inside the dev container runs using a local configuration file. See the [[tba_dev_config.json|tba_dev_config]] documentation for more details.

## Bootstrapping Data

There are two ways to import data into a local development environment. You can either bootstrap the local db from the production site, or run the datafeeds locally to fetch data directly from FIRST.

### Bootstrapping from Prod TBA

When running locally, TBA will export a bootstrap interface at [http://localhost:8080/local/bootstrap](http://localhost:8080/local/bootstrap). You need to have an API key for the Read APIv3 on prod, which you can obtain on [your account page](https://www.thebluealliance.com/account). Then, you can choose which data you want to import by inputting its data key.

### Bootstrapping from FIRST

(TODO not implemented yet)

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
$ docker pull ghcr.io/the-blue-alliance/the-blue-alliance/tba-py3-dev:latest
$ vagrant up
```

If you have problems destroying your container via Vagrant, you can remove the container via Docker.

```
$ docker stop tba
$ docker rm tba
$ vagrant up
```

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

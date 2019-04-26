# Development Environment Setup

We have a development container setup that uses [`vagrant`](https://www.vagrantup.com/)+[`docker`](https://www.docker.com/). This approach lets us isolate all the dependencies for running an instance of TBA. Before you start, be sure you have forked this repository to your own account namespace and cloned the code. If this process is new to you, check out GitHub's guides for [forking](https://guides.github.com/activities/forking/) and the [contributing workflow](https://guides.github.com/introduction/flow/).  
## Install Dependencies

You should be able to install `docker` and `vagrant` from your system's package manager (Homebrew, `apt`, etc.).

Ensure that the version of `vagrant` is at least `2.1.0` (run `vagrant --version` to confirm). Some linux distributions, like Debian, may not always have the newest version available in the repositories. If that's the case, you may need to install `vagrant` from [the website](https://www.vagrantup.com).

This is optional, but you may also want to configure running `docker` as a non-root user and to automatically start on system boot. You can find instructions [here](https://docs.docker.com/engine/installation/linux/linux-postinstall/).

## Start the Container

 1. Ensure the `docker` daemon is running: `sudo service docker start`
 2. Start and bootstrap the container: `vagrant up --provider=docker`. The first time this runs, it may install supplemental plugins. After that, run the same command again to actually start the container.
 3. Begin automatically syncing local files into the container: `vagrant rsync-auto`

You should now be able to access a local instance of TBA at `localhost:8080`. If you need, the App Engine admin panel should be accessable at `localhost:8000`.

## Connecting to the Container

Many times, you will need to run commands inside the dev container. You can `ssh` into the container by running `vagrant ssh`. Then, run `tmux attach` to bring up the [`tmux`](http://man.openbsd.org/OpenBSD-current/man1/tmux.1) session. There will be three windows: a shell, the GAE devserver, and gulp running. You can use `^B-<window number>` to switch between windows and `^B-d` to detach from `tmux`. It is important to leave `tmux` running, since it hosts the development server.

## Rebuilding Resources

If you make changes to javascript or css files, you may have to recompile them. Inside the container, run `paver make` from within the `tba` directory.

## Bootstrapping Data

Inside the container, you can run `paver bootstrap` from within the `tba` directory to load production data into your development instance. This will load the 2016 New England District Championship by default (which you can access at localhost:8080/event/2016necmp). You can load a different event by passing it's event key (e.g. `2016necmp`) to `paver bootstrap` (e.g. `paver bootstrap --key=2016necmp`). You will need to provide your TBA APIv3 key in order to load data, you can generate one at https://www.thebluealliance.com/account.

If you have any third-party API keys (such as for the FRC API), you can input them at localhost:8080/admin/authkeys. You can also request FRC API keys [here](https://frc-events.firstinspires.org/services/API).

## Running Tests/Lint

Before you submit your code changes, you should run the project test suite to make sure all tests pass. Inside the container, you can run `paver test` to run the suite. You can also run `paver lint` to make sure the code passes quality standards.

## Dev Issues

### Reprovision Your Container

If you run into issues, especially after not working with your dev instance for a while, try reprovisioning and restarting your container.

```
$ vagrant halt
$ vagrant destroy
$ vagrant up --provider=docker
```

If you have problems destroying your container via Vagrant, you can remove the container via Docker.

```
$ docker stop tba
$ docker rm tba
$ vagrant up --provider=docker
```

The name of your Docker container should always be `tba`. If it's not, you can find it by listing all containers.

```
$ docker container ls
```

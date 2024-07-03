## Initial setup

1. Install WSL 2 running Ubuntu 22.04.
2. Install Docker Desktop on Windows.
3. Open Docker Desktop -> Settings -> General -> Enable `Use the WSL 2 based engine`
4. Open Docker Desktop -> Settings -> Resources -> WSL integration -> enable integration with all repos (if this doesn't show up, install the Docker CLI on your ubuntu distro and restart Docker Desktop)
5. Make sure to hit `Apply & Restart` on Docker Desktop
6. Fork and clone TBA's source on the `py3` branch
7. Run `docker compose up -d`. This will begin to bring up the TBA stack in the background. After a few minutes, you'll be able to reach `localhost:8000` and various other ports.

### Console logs

In order to view console logs, you need to SSH into the container.

```bash
# First, check that the docker bringup has concluded
wsl:$ docker compose logs
# ... snipped for brevity ...
tba-1  | 2: datastore (1 panes) [80x24] [layout b25f,80x24,0,0,2] @2
tba-1  | 3: webpack (1 panes) [80x24] [layout b260,80x24,0,0,3] @3
tba-1  | 5: firebase- (1 panes) [80x24] [layout b261,80x24,0,0,4] @4
tba-1  | To view logs and auto-update files, run `./ops/dev/host.sh`

# This assumes that TBA is the most recent thing you've brought up
# Next, run bash in an interactive terminal on the container
wsl:$ docker exec -it $(docker container ls --latest --quiet) /bin/bash
root@tba:/tba$

# Now that you are in, you can attach to the existing tmux session
root@tba:/tba$ tmux attach
```

### App Engine Admin Console

If you navigate to `localhost:8000` with your Windows browser, you'll arrive at the GAE dev app server. Unfortunately, you can't actually perform any tasks, because the buttons on the console will attempt to POST to `localhost:8000`, but Google's dev server is written to reject any requests with an origin header of `0.0.0.0:8000`. The easiest way to get around this is to run a browser **inside** WSL2 via:

```bash
wsl:$ sensible-browser
```

which should spawn a WSL-native GUI app (Chrome or Firefox) that is running on WSL itself. This will then allow you to connect to the console through `0.0.0.0:8000`. The alternative is to set up port forwarding if you have the knowledge to do so.

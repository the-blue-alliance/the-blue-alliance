## Initial setup

1. Install WSL 2 running Ubuntu 22.04.
2. Install Docker Desktop on Windows.
3. Open Docker Desktop -> Settings -> General -> Enable `Use the WSL 2 based engine`
4. Open Docker Desktop -> Settings -> Resources -> WSL integration -> enable integration with all repos (if this doesn't show up, install the Docker CLI on your ubuntu distro and restart Docker Desktop)
5. Make sure to hit `Apply & Restart` on Docker Desktop
6. Fork and clone TBA's source
7. Run `docker compose up --build -d`. This will begin to bring up the TBA stack in the background. After a few minutes, you'll be able to reach `localhost:8080` and various other ports.

### Console logs

View logs directly via `docker compose`:

```bash
# Follow all service logs
wsl:$ docker compose logs -f

# Follow logs for a specific service
wsl:$ docker compose logs -f tba
wsl:$ docker compose logs -f webpack
```

To get a shell inside the container:

```bash
wsl:$ docker compose exec tba bash
```

### App Engine Admin Console

If you navigate to `localhost:8000` with your Windows browser, you'll arrive at the GAE dev app server. Unfortunately, you can't actually perform any tasks, because the buttons on the console will attempt to POST to `localhost:8000`, but Google's dev server is written to reject any requests with an origin header of `0.0.0.0:8000`. The easiest way to get around this is to run a browser **inside** WSL2 via:

```bash
wsl:$ sensible-browser
```

which should spawn a WSL-native GUI app (Chrome or Firefox) that is running on WSL itself. This will then allow you to connect to the console through `0.0.0.0:8000`. The alternative is to set up port forwarding if you have the knowledge to do so.

## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow the following steps to bump the Python version -

1) Update the [`runtime` directive in the service `.yaml` files](https://cloud.google.com/appengine/docs/standard/python3/config/appref)
2) Update the [`python-version`](https://docs.github.com/en/actions/guides/building-and-testing-python#specifying-a-python-version) in the GitHub Actions (`.github/workflows/*.yml`) files
3) Update the [[Repo Setup|Repo-Setup]] docs to reflect the new Python version

## Clearing Redis Cache

### Automatically

There is a convenience script which will drop you into a `redis-cli` interface. It essentially does the manual steps below.

```bash
> ./ops/shell/memorystore_shell.sh
```

When you're done, you can disconnect from the shell using a SIGINT (`Control` + `C`). Make sure the cleanup executes successfully! We're billed for the Compute Engine instance uptime, so making sure the Compute Engine instance is shut down is important.

### Manually

Currently there is no interfacing for clearing the Redis cache - it must be cleared manually. This involves SSHing in to a machine on the `tba-memorystore` network, connecting to the Redis instance via `redis-cli`, and clearing the cache.

First, enable SSH access on the [`tba-memorystore`](https://console.cloud.google.com/networking/networks/details/tba-memorystore) network. There is a pre-configured firewall rule that will allow traffic on port 22. Click `Firewall rules` -> `tba-memorystore-allow-ssh` -> `Edit`, and under `Enforcement` select `Enabled`. Click `Save` for the changes to go in to effect.

In the [Compute Engine/VM Instances](https://console.cloud.google.com/compute/instances) section, there is a pre-configured VM instance called `redis-telnet-vm`. Start the VM instance. Once the instance is booted, click the `SSH` and select a method of connecting to the instance. Using the gcloud command is recommended, but any of the methods will work.

After connecting to the VM, connect to the Redis instance via `redis-cli`. The command with the IP address should be in the bash history of the VM. Otherwise, you can find the IP address on the [Redis memorystore page](https://console.cloud.google.com/memorystore/redis/instances).

```bash
> redis-cli -h {ip_address}
```

Once connected, you can either search for a key to delete and delete the specified key, or delete the entire cache. To delete the entire cache, use the `FLUSHALL` command.

```
$ FLUSHALL
```

To find a specific key, use the `keys` command and wildcards in order to find the key name you're looking for.

```bash
$ keys *flask*
```

After finding the key, delete the key using the `del` command.

```bash
$ del "{key}"
```

Disconnect from the Redis instance and the VM. Afterwards, make sure to roll-back the setup done earlier -

1) Stop the `redis-telnet-vm` VM
2) Disable the `tba-memorystore-allow-ssh` firewall rule


## Building a New Development Container Version

We host built container images with [Google Cloud Build](https://cloud.google.com/cloud-build). The build config and `Dockerfile` are [in the repo](https://github.com/the-blue-alliance/the-blue-alliance/tree/py3/ops/dev/docker). After the `Dockerfile` is updated, we'll need to rebuild + push the image:

```bash
# Locally, you need gcloud and docker installed
$ ./ops/dev/docker/build-container-images.sh
```

Images are published to `gcr.io/tbatv-prod-hrd/tba-py3-dev` and can be managed from the [cloud console](https://console.cloud.google.com/gcr).

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.** After modifying the database, be sure to clear the Redis cache to remove any stale cached data.

## Before using a deferred task, consider `run_after_response`

Deferred tasks are used to handle expensive tasks asynchronously in order to not block the serving of a response for a request. Before using a deferred task, consider the importance of retrying the task if an error should occur. If it's okay for the task to fail silently without retries (e.g. tracking an API request call), `backend.common.run_after_response` is a lighter-weight solution that is more appropriate.

Usage examples:

```python
run_after_response(lambda: ...)
```

```python
run_after_response(function_to_run)
```

```python
@run_after_response
def function_to_run():
    ...
```

## Deferred Tasks

The Blue Alliances leverages [Google Cloud Task](https://cloud.google.com/tasks/docs/dual-overview) for deferred work. Examples of this work include any post-request tasks that need retrying should an error occur, such as dispatching push notifications. Locally, Google Cloud Tasks can be used by round-tripping requests upstream back to a local development container via ngrok, or more commonly swapped out for Redis/RQ.

`defer` is a drop-in replacement for [google.appengine.ext.deferred.deferred.defer](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.ext.deferred.deferred). `defer` enqueues a method to be run later while automatically managing dispatching to the proper client based on the environment, getting a queue for a specified queue name, etc. Using `defer` is recommended unless you need some more fine-tuned control over tasks/queues. `defer` manages executing a task with the proper parameters both in development and in production. If an option is not supported in `defer` that is supported in the Google Cloud Task API protos, it is recommend to build this functionality in to `defer` and then leverage `defer`.

### Configuring Services for `defer`

Tasks executed with `defer` are just HTTP requests that are serialized + executed at a later time. By default, these tasks will use a use a `/_ah/queue/deferred.*` route when executing. A catch-all route for requests matching this regex can be installed for Flask apps by using the `install_defer_routes` method.

```python
from flask import Flask

from backend.common.deferred.handlers import install_defer_routes

app = Flask(__name__)
install_defer_routes(app)
```

### Deferring Tasks

Deferred tasks tend to be expensive tasks that can happen asynchronously in order to expedite serving a response for a request.

```python
from from backend.common.deferred import defer

def do_expensive_work(a, *, b):
    ...

defer(do_expensive_work, "a", b="c")
```

---

The `defer` method can also take several arguments to better control how deferred tasks should execute.

| Parameter | Description |
| --- | --- |
| `_client` | A `backend.common.deferred.clients.task_client` instance that manages creating a queue. If this is not specified, `defer` will create a client based on the current environment. |
| `_target` | The service which the executed task should be run on. If this is not specified, `defer` will attempt to run the task on the service that enqueued the task. |
| `_url` | The URL that the task should hit. This expects a partial URL (path + query). If this is not specified, tasks will use the `/_ah/queue/deferred` URL. |
| `_headers` | Any headers that should be passed along to the executing request handler. Currently these headers are unused. |
| `_queue` | The queue which the task should be enqueued in. If this is not specified, tasks will be enqueued in the `default` queue. |

---

An in-depth example making use of these parameters might be a task that needs to be deferred to execute on a vanity URL for logging + metrics and on a different service than the service that is enqueueing the task to be executed on a specific queue.

```python
def do_something():
    ...

defer(do_something, _target="tasks-io", _url="/_ah/queue/deferred_do_something", _queue="do-something-queue")
```

## Creating Queues

Queues and queue configurations are managed via the `queue.yaml` file. Queues and their configurations will be created/updated during deploys. Queues removed from this file will not be deleted. Queues must be deleted manually from the web interface.

For details on setting up queues to match a production instance, see the [Task Queues section of the Google App Engine + Firebase setup page](https://github.com/the-blue-alliance/the-blue-alliance/wiki/GAE-Firebase-Setup#task-queues).

### `queue.yaml` syntax

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `max_dispatches_per_second` | float | | The maximum rate at which tasks are dispatched from this queue. |
| `max_concurrent_dispatches` | int | 0 | The maximum number of concurrent tasks that Cloud Tasks allows to be dispatched for this queue. After this threshold has been reached, Cloud Tasks stops dispatching tasks until the number of outstanding requests decreases. |
| `max_attempts` | int | -1 | The maximum number of attempts per task in the queue. Set to `0` for no re-attempts. Set to `-1` for unlimited attempts. |
| `max_retry_duration_seconds` | int | | The time limit in seconds for retrying a failed task, measured from when the task was first run. Once the `--max-retry-duration` time has passed and the task has been attempted `--max-attempts` times, no further attempts will be made and the task will be deleted. |
| `min_backoff_seconds` | int | | The minimum amount of time in seconds to wait before retrying a task after it fails. |
| `max_backoff_seconds` | int | | The maximum amount of time in seconds to wait before retrying a task after it fails. |
| `max_doublings` | int | | The time between retries will double maxDoublings times. A tasks retry interval starts at minBackoff, then doubles maxDoublings times, then increases linearly, and finally retries retries at intervals of maxBackoff up to maxAttempts times. |

See the [gcloud tasks queues create](https://cloud.google.com/sdk/gcloud/reference/tasks/queues/create) or [gcloud tasks queues update](https://cloud.google.com/sdk/gcloud/reference/tasks/queues/update) command documentation for details.

## Local Development

### Redis + RQ

In development, `defer` use Redis + RQ as opposed to Google Cloud Tasks to execute deferred tasks. A Redis server, RQ worker, and dashboard are spun up when the development container is booted and can be seen when attaching to the container's tmux session. The RQ Dashboard can be found at [0.0.0.0:9181](http://0.0.0.0:9181/) be used to monitor failed tasks. Tasks that execute successfully will not show up in the RQ Dashboard, but they can be seen as successfully executed in the `rq-worker` tmux tab.

### Google Cloud Tasks + ngrok

Sometimes, Google Cloud Tasks semantics are necessary when testing a feature. It is possible to enqueue a task from a local development instance to an upstream project's Google Cloud Tasks queue to be executed in the local development instance. This process leverages [ngrok](https://ngrok.com/) to expose a public URL that routes back to the host machine.

You'll need an upstream Google App Engine instance, along with the queues created upstream. Refer to the [[Google App Engine + Firebase Setup|GAE-Firebase-Setup]] for details.

Download [ngrok](https://ngrok.com/) and run `ngrok` with the `http` command + the port you want to forward traffic to. The port is the port associated with your service in the development container. Ex: At the time of writing, the `py3-tasks-io` service is the 4th service started, so it maps to `8084` (or `http://localhost:8084`).

```shell
$ ./ngrok http 8084
...
Forwarding  http://a0e8a1c75a5e.ngrok.io -> http://localhost:8084
```

Change the `tasks_mode` property in [`tba_dev_config.json`/`tba_dev_config.local.json`](https://github.com/the-blue-alliance/the-blue-alliance/wiki/tba_dev_config) to be `remote`, and add a `tasks_remote_config` dictionary with a `ngrok_url` key/value. The value should be the URL for your ngrok URL. Additionally, set the `google_application_credentials` field (details can be found in the [[development runbook|Development-Runbook]]).

```json
{
    ...
    "google_application_credentials": "ops/dev/keys/my-key.json",
    "tasks_mode": "remote",
    "tasks_remote_config": {
        "ngrok_url": "http://a0e8a1c75a5e.ngrok.io"
    },
    ...
}
```

After syncing over your modified config file, make sure to either restart your dev container or restart the `dev_appserver.sh` script in the tmux session in order to get the local project to respect the modified config file.

Finally, execute the code that defers a task locally. Success/failure of tasks along with logs should be available in the [Google Cloud Tasks Dashboard](https://console.cloud.google.com/cloudtasks). If your task is not being enqueued upstream or the task is failing to execute properly downstream, check for logs in the `gae` tmux tab. If you suspect your task is failing to route properly to your local development contianer, check ngrok for any errors.


## Testing Queues + defer

A `FakeTaskClient`, which uses an in-memory Redis stub, can be used during test to mock queues. `FakeTaskClient` is a singleton and calling the initializer will give you the singleton instance. By default, using `defer` will use the `FakeTaskClient` during tests. The `FakeTaskClient` instance is available via a pytest fixture as well for convenience.

`FakeTaskClient` exposes two methods - `pending_job_count` and `drain_pending_jobs`. `pending_job_count` can be used to test that jobs have been enqueued for a given queue, and `drain_pending_jobs` can be used to run all jobs on a given queue. `drain_pending_jobs` does *not* require that a webapp is running to process requests - it will run enqueued functions without going through the usual HTTP routing used for Google Cloud Tasks/RQ tasks.

```python
def test_enqueue(task_client: FakeTaskClient) -> None:
    def do_something() -> None:
        pass

    assert task_client.pending_job_count("testing") == 0

    defer(do_something, _queue="testing")

    assert task_client.pending_job_count("testing") == 1

    task_client.drain_pending_jobs("testing")
```

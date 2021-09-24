The Blue Alliances leverages [Google Cloud Task](https://cloud.google.com/tasks/docs/dual-overview) for deferred work. Examples of this work include any post-request tasks that need retrying should an error occur, such as dispatching push notifications. Locally, Google Cloud Tasks can be used by round-tripping requests upstream back to a local development container via ngrok, or more commonly swapped out for Redis/RQ.

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

## Deferred Tasks (`defer`)

`defer` is a drop-in replacement for [google.appengine.ext.deferred.deferred.defer](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.ext.deferred.deferred). Deferred tasks tend to be expensive tasks that can happen asynchronously in order to expedite serving a response for a request. `defer` enqueues a `Callable` method to be executed later while automatically managing dispatching to the proper client (Google Cloud Tasks/Redis) based on the environment, getting a queue for a specified queue name, etc. Using `defer` is recommended unless you need some more fine-tuned control over service execution, tasks, or queues. `defer` manages executing a task with the proper parameters both in development and in production.

### Configuring Services for `defer`

Tasks executed with `defer` are serialized `Callable` functions that are stored and executed at a later time via a HTTP request to the specified service. By default, these tasks will use a use a `/_ah/queue/deferred.*` route when executing. A catch-all route for requests matching this regex can be installed for Flask apps by using the `install_defer_routes` method.

```python
from flask import Flask

from backend.common.deferred.handlers import install_defer_routes

app = Flask(__name__)
install_defer_routes(app)
```

Failing to install this route on the service executing deferred tasks will lead to tasks failing. When using Google Cloud Tasks, the failed task will be retried continuously. Specifying a URL that doesn't follow the `/_ah/queue/deferred.*` pattern/routing to a different URL on the service and attempting to execute the deferred task manually is dangerous, as this bypasses the security mechanisms built-in to the `deferred` endpoints + executing deferred tasks. More about these security considerations in [`defer` Security](#defer Security).

### Deferring Tasks

```python
from backend.common.deferred import defer

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

### `defer` Security

Executing a deferred task request requires some additional security in order to prevent against remote code execution. Tasks being executed via the deferred task handler will check to make sure either a `X-AppEngine-TaskName` or a `X-Google-TBA-RedisTask` header is present. The [`X-AppEngine-TaskName` header](https://cloud.google.com/tasks/docs/creating-appengine-handlers#reading_app_engine_task_request_headers) is added by Google Cloud Tasks when executing a deferred task. A bogus `X-AppEngine-TaskName` header from an attacker will be dropped by App Engine. The [`X-Google-TBA-RedisTask` header](https://cloud.google.com/appengine/docs/standard/python3/reference/request-response-headers) is added to local tasks being stored in Redis and executed later by rq. The `X-Google-*` prefix ensures that if an attacker attempts to send a bogus `X-Google-TBA-RedisTask` header to a deferred route in production, the header will be dropped by App Engine.

### ⚠️ Pitfalls and Warnings with `defer` ⚠️

`defer` allows for executing code across service boundaries. For instance - a task (a `Callable` function in Python) can be deferred from `web` but executed on a different service by specifying a different service with the `_target` parameter. Cross-service code execution can fail due to missing imports or missing code on the executing service. Ex: The `Callable` function might depend on an import from the service it originated on (in our instance, `web`) that is not available on the executing service. When using `defer` for enqueueing work on a different service, be mindful the code will not be executing in the same environment it was enqueued from.

The safer approach for deferring cross-service work is to create a HTTP endpoint on the target service and use [`enqueue`](#Enqueued Tasks) to call the HTTP endpoint at a later date. The HTTP request will be made on the specified service (or by default the enqueueing service), but the work will always be executed on the target service.

## Enqueued Tasks (`enqueue`)

`enqueue` is a drop-in replacement for [google.appengine.api.taskqueue.taskqueue.add](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.taskqueue.taskqueue#google.appengine.api.taskqueue.taskqueue.add). `enqueue` tasks tend to be expensive tasks to be executed across service boundaries that can happen asynchronously in order to expedite serving a response for a request. `enqueue` enqueues a HTTP request to be run later while automatically managing dispatching to the proper client based on the environment, getting a queue for a specified queue name, etc. Using `enqueue` is recommended for cross-service requests. `enqueue` manages executing a task with the proper parameters both in development and in production.

### Configuring Services for `enqueue`

Tasks executed with `enqueue` are HTTP requests that are executed at a later time against the designated service. An endpoint should be built out as normal on the designated service to handle the request with the desired routing.

Services that will be servicing enqueued tasks need to call `install_backend_security` in order to install the security checks that will be run before executing enqueued tasks. It's worth noting - installing these security mechanisms on a Flask app will restrict the app from handling any public requests. The Flask app will only be able to handle Task Queue tasks (from Google Cloud Tasks or Redis/rq), cron tasks, or requests with an [`Authorization: Bearer` token](https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-app-identity) from a valid App Engine project. More details on this additional security can be found in [`enqueue` Security](#enqueue Security).

```python
# backend.py
from flask import Flask

from backend.common.middleware import install_backend_security

app = Flask(__name__)
install_backend_security(app)

@app.route("/do_expensive_work")
def do_expensive_work():
    # Do some work here...
    return "Work done!"
```

### Enqueueing Tasks

```python
from backend.common.deferred import enqueue

enqueue(url='/backend/do_expensive_work', target='backend', params={"abc": "efg"})
```

The `enqueue` method can also take several arguments to better control how enqueued tasks should execute.

| Parameter | Description |
| --- | --- |
| `url` | The URL that the task should hit. This expects a partial URL. |
| `headers` | Any headers that should be passed along to the executing request handler. Note: These headers are *not* passed to the called endpoint. |
| `method` | The HTTP method that should be used when hitting the specified endpoint. Only `GET` and `POST` are supported. |
| `params` | A dictionary that will be passed to endpoints with the `POST` method as urlencoded form data. This field is unused in the case of `GET` requests. |
| `queue_name` | The queue which the task should be enqueued in. If this is not specified, tasks will be enqueued in the `default` queue. |
| `target` | The service which the executed task should be run on. Note: The "task" in this sentence is making the HTTP request. The HTTP request will be executed on the service that the specified endpoint routes to. If this is not specified, `enqueue` will attempt to run the task on the service that enqueued the task. |

### `enqueue` Security

Executing an enqueued task requires some additional security in order to prevent against remote code execution. Before the request is handled, the task is validated as either coming from a task queue source (Google Cloud Tasks via the presence of the `X-AppEngine-TaskName` header, or Redis/rq via the presence of the `X-Google-TBA-RedisTask` header), a cron source (via the presence of the `X-Appengine-Cron` header), or from a verified originator (via the presence of a `Authorization` header). For the `X-App(E|e)ngine-*` and `X-Google-*` headers, App Engine will remove these headers if sent from a non-App Engine source, which prevents attackers from attempting to provide these headers to bypass this check.

The `Authorization` header validation is from Google's [OpenID Connect ID Token](https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-app-identity) guide. The `Authorization` header should contain an OAuth 2 `Bearer` token which has been signed by the Google Cloud runtime environment (or TBA when working in development - more on this later). The `Bearer` token is validated as having been issued by Google's OAuth 2.0 authorization server. Next, the service account email that signed the request is verified as being from the same project that is executing it (in dev this is `test`, in production this is the production project ID) and coming from an App Engine service account. If all of these checks pass, the request moves on to being handled.

In development (when using the `test.json` `google_application_credentials` key) we mock the token vendor endpoint locally to generate an `Bearer` token using fake credentials that will pass using the same validation used in production. This endpoint is *not* live in production, and tokens generated via this endpoint in production would still fail validation in production.

Finally, tasks being executed via the enqueued task handler will check to make sure either a `X-AppEngine-TaskName` or a `X-Google-TBA-RedisTask` header is present - the same headers used for [`defer` Security](#defer Security).

## `run_after_response` vs `defer` vs `enqueue`

This page outlines three different methods for executing code (a "task") at a later date - `run_after_response`, `defer`, and `enqueue`. When should each one of these methods be used?

**`run_after_response`** should be used when a task is lightweight, can be run on the calling service, should be allowed to fail silently, and does not need to be retried. Examples include posting analytics to Google Analytics. `run_after_response` should always be considered first when considering how to run code later, since using `run_after_response` takes weight off the task queues. If a task is not running in the context of a Flask request, `run_after_response` cannot be used (although those cases are rare in The Blue Alliance codebase).

**`defer`** should be used when a task can be run on the calling service *or* the target service without import issues, should be retried according to a queue's retry mechanics, and should produce some error that can be monitored. `defer` mechanics are safer for same-service execution than `enqueue` since a URL must be passed to `enqueue` that aligns with a URL on another service that may change without notice. `defer` cannot be used in a variety of situations, including if a payload is too big to be serialized for Google Cloud Tasks, if the executing service needs access to code not available on that service (ex: code enqueued on `web` but executed on `tasks-io` will not have access to the `web` code when being executed), or when multiple levels of authentication must be present when enqueueing a task (ex: tasks have no idea of "admin" authentication - this authentication should be done *before* enqueueing the task on the `web` service).

**`enqueue`** should be used for any situation not covered by `run_after_response` and `defer`.

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

Note: The rq worker must be invoked with a list of queues to execute tasks on. The current list of supported queues can be found in the [`start-devserver.sh`](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/ops/dev/vagrant/start-devserver.sh) script. If tasks are being deffered locally on an unsupported queue, add the queue to the list of queues the rq worker should monitor and restart the worker.

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

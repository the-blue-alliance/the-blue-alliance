## Queues + defer

The Blue Alliances leverages [Google Cloud Task](https://cloud.google.com/tasks/docs/dual-overview) for deferred work. Examples of this work include tracking API request calls, dispatching push notifications, any post-request tasks, etc. Locally, Google Cloud Tasks can be used by round-tripping requests upstream back to a local development container via ngrok, or more commonly swapped out for Redis/RQ.

`defer` is a drop-in replacement for [google.appengine.ext.deferred.deferred.defer](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.ext.deferred.deferred). `defer` enqueues a method to be run later while automatically managing dispatching to the proper client based on the environment, getting a queue for a specified queue name, etc. Using `defer` is recommended unless you need some more fine-tuned control over tasks/queues. `defer` manages executing a task with the proper parameters both in development and in production. If an option is not supported in `defer` that is supported in the Google Cloud Task API protos, it is recommend to build this functionality in to `defer` and then leverage `defer`.

### Configuring Services for `defer`

Tasks executed with `defer` are just HTTP requests that are serialized + executed at a later time. By default, these tasks will use a use a `/_ah/queue/deferred.*` route when executing. A catch-all route for requests matching this regex can be installed for Flask apps by using the `install_defer_routes` method.

```
from flask import Flask

from backend.common.deferred.handlers import install_defer_routes

app = Flask(__name__)
install_defer_routes(app)
```

### Deferring Tasks

Deferred tasks tend to be expensive tasks that can happen asynchronously in order to expedite serving a response for a request.

```
from from backend.common.deferred import defer

def do_expensive_work(a, *, b):
    ...

defer(do_expensive_work, "a", b="c")
```

The `defer` method can also take several arguments to better control how deferred tasks should execute.

`_client` - A `backend.common.deferred.clients.task_client` instance that manages creating a queue. If this is not specified, `defer` will create a client based on the current environment.
`_target` - The service which the executed task should be run on. If this is not specified, `defer` will attempt to run the task on the service that enqueued the task.
`_url` - The URL that the task should hit. This expects a partial URL (path + query). If this is not specified, tasks will use the `/_ah/queue/deferred` URL.
`_headers` - Any headers that should be passed along to the executing request handler. Currently these headers are unused.
`_queue` - The queue which the task should be enqueued in. If this is not specified, tasks will be enqueued in the `default` queue.

## Creating Queues

Queues must be created in Google App Engine [using the gcloud command](https://cloud.google.com/tasks/docs/creating-queues). The linked document should be the source of truth for creating queues.

Currently there is no automated tooling for creating/updating queues in production. The list below describes how to get setup the current production queues.

```
$ gcloud tasks queues create admin --max-dispatches-per-second 5 --max-attempts -1
$ gcloud tasks queues create api-track-call --max-dispatches-per-second 500 --max-attempts 1
$ gcloud tasks queues create backups --max-dispatches-per-second 0.1 --max-concurrent-dispatches 1 --max-attempts -1
$ gcloud tasks queues create cache-clearing --max-dispatches-per-second 5 --max-attempts -1
$ gcloud tasks queues create datafeed --max-dispatches-per-second 5 --max-attempts -1 --max-retry-duration 3600s
$ gcloud tasks queues create default --max-dispatches-per-second 10 --max-attempts 1
$ gcloud tasks queues create firebase --max-dispatches-per-second 50 --max-attempts -1
$ gcloud tasks queues create post-update-hooks --max-dispatches-per-second 5 --max-attempts -1
$ gcloud tasks queues create push-notifications --max-dispatches-per-second 100 --max-attempts -1 --max-retry-duration 180s --min-backoff=10s --max-backoff=30s
$ gcloud tasks queues create run-in-order --max-dispatches-per-second 5 --max-concurrent-dispatches 1 --max-attempts -1
$ gcloud tasks queues create search-index-update --max-dispatches-per-second 10 --max-attempts -1
```

Queues can be updated using the `gcloud tasks queues update {queue_name}` command. See `gcloud tasks queues update --help` for all available options. Alternatively, these properties can be updated in the Google Cloud Tasks interface.

As a note - the production legacy queues have a `--max-concurrent-dispatches` value of `0`, where newly created queues must have a non-zero value for this field. The default value is `1000`, and the maximum value is `5000`. The commands above leave the the `max-concurrent-dispatches` value to the default. However, this might be too low for some use cases, and can be increased as necessary.

## Local Development

### Redis + RQ

In development, `defer` use Redis + RQ as opposed to Google Cloud Tasks to execute deferred tasks. A Redis server, RQ worker, and dashboard are spun up when the development container is booted and can be seen when attaching to the container's tmux session. The RQ Dashboard can be found at [0.0.0.0:9181](http://0.0.0.0:9181/) be used to monitor failed tasks. Tasks that execute successfully will not show up in the RQ Dashboard, but they can be seen as successfully executed in the `rq-worker` tmux tab.


### Google Cloud Tasks + ngrok

Sometimes, Google Cloud Tasks semantics are necessary when testing a feature. It is possible to enqueue a task from a local development instance to an upstream project's Google Cloud Tasks queue to be executed in the local development instance. This process leverages [ngrok](https://ngrok.com/) to expose a public URL that routes back to the host machine.

You'll need an upstream Google App Engine instance, along with the queues created upstream. The former is out of scope for this document, and the latter is documented above.

Download [ngrok](https://ngrok.com/) and run `ngrok` with the `http` command + the port you want to forward traffic to. The port is the port associated with your service in the development container. Ex: At the time of writing, the `py3-tasks-io` service is the 4th service started, so it maps to `8084` (or `http://localhost:8084`).

```
$ ./ngrok http 8084
...
Forwarding  http://a0e8a1c75a5e.ngrok.io -> http://localhost:8084
```

Change the `tasks_mode` property in `tba_dev_config.json`/`tba_dev_config.local.json` to be `remote`, and add a `tasks_remote_config` dictionary with a `ngrok_url` key/value. The value should be the URL for your ngrok URL. Additionally, set the `google_application_credentials` field (details can be found in the [[development runbook|Development-Runbook]]).

```
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

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

The Blue Alliances leverages [Google Task Queue](https://cloud.google.com/appengine/docs/standard/python/taskqueue) for deferred work. Examples of this work include any post-request tasks that need retrying should an error occur, such as dispatching push notifications.

[`deferred.defer`](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.ext.deferred.deferred) is a simple way of executing a task later. A `Callable` in Python is serialized and run later on the specified service. `deferred.defer` should be used unless full task queue semantics are required.

### Configuring Services for `deferred.defer`

Flask apps must pass `use_deferred=True` in the call to `wrap_wsgi_app()`

```python
from flask import Flask
from google.appengine.api import wrap_wsgi_app
from google.appengine.ext import deferred

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
```

Additionally, the service `yaml` file should be configured to only execute authenticated deferred tasks.

```yaml
service: service

...

handlers:
  - url: /_ah/queue/deferred.*
    script: auto
    login: admin
  - url: .*
    script: auto
```

### Using `deferred.defer`

```python
from google.appengine.ext import deferred

def do_expensive_work(a, *, b):
    ...

@app.route("/do_the_thing")
def do_the_thing():
    deferred.defer(do_expensive_work, "a", b="c")
    return "Done! deferred expensive work for later."
```

See the [`google.appengine.ext.deferred.deferred` module documentation](https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.ext.deferred.deferred) for a full list of parameters available for `deferred.defer`.

### Using custom `deferred.defer` routes

By default, tasks will dispatch to the `/_ah/queue/deferred` route via the `default` queue. To use a vanity URL starting with `/_ah/queue/deferred` but having a custom suffix (ex: `/_ah/queue/deferred_manipulator_clearCache`), we can install a custom catch-all regex handler on the service.

```python
from flask import Flask
from google.appengine.api import wrap_wsgi_app
from google.appengine.ext import deferred

from backend.common.deferred import install_defer_routes

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app, use_deferred=True)
install_defer_routes(app)

@app.route("/do_later")
def do_later():
    deferred.defer(clear_the_cache, _url="/_ah/queue/deferred_manipulator_clearCache")
    return "Done! deferred expensive work for later."
```

Custom URLs can be supported as well using a more manual process. A route must be created that calls to `deferred.application` to handle the original request. This is not recommended, but can be done.

```python
@app.route("/do_the_thing")
def do_the_thing():
    # Providing a custom URL.
    # Handle requests routed to this endpoint.
    deferred.defer(do_something_later, _url="/custom/path")
    return "Done! deferred expensive work for later."

@app.route("/custom/path", methods=["POST"])
def custom_deferred_handler():
    # request.environ contains the WSGI `environ` dictionary (See PEP 0333)
    # application.post() executes the default deferred task execution logic
    return deferred.application.post(request.environ)
```

### Testing `deferred.defer`

See Google's documentation for writing taskqueue tests and [writing deferred task tests](https://cloud.google.com/appengine/docs/standard/python/tools/localunittesting#deferred-tasks). A `taskqueue_stub` is available for method-based tests that make use of `src/backend/conftest.py`.

```python
from google.appengine.ext import deferred

def test_defer(taskqueue_stub) -> None:
    def do_something() -> None:
        pass

    # Assert no tasks in the queue
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="testing")
    assert len(tasks) == 0

    # Add a task to the queue
    deferred.defer(do_something, _queue="testing")

    # Assert task has been added to the queue
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="testing")
    assert len(tasks) == 1

    # Execute tasks - queue will *not* be drained automatically after executing
    for task in tasks:
        deferred.run(task.payload)
```

Class-based `unittest.TestCase` tests can pull the `pytest` test fixture on to the class via an additional method.

```python
import unittest
from typing import Optional

import pytest
from google.appengine.ext import testbed

class ClassBasedTest(unittest.TestCase):
      taskqueue_stub: Optional[testbed.taskqueue_stub.TaskQueueServiceStub] = None

      @pytest.fixture(autouse=True)
      def store_taskqueue_stub(self, taskqueue_stub):
          self.taskqueue_stub = taskqueue_stub
```

If the Class-based test does not necessarily need to capture/use the `taskqueue` stub but needs to setup the `taskqueue` stub for some downstream code, the fixture can be used without assigning to a variable.

```python
import unittest

import pytest

@pytest.mark.usefixtures("taskqueue_stub")
class ClassBasedTest(unittest.TestCase):
    ...
```

## Managing Queues

Queues and queue configurations are managed via the [`queue.yaml` file](https://cloud.google.com/appengine/docs/standard/python/config/queueref). Changes to the `queue.yaml` file will be deployed when the site is deployed via CI.

## Using Queues

Details on using queues directly will not be covered in this doc, since it is not the recommended way for deferring work for most cases. Refer to [Google's taskqueue documentation](https://cloud.google.com/appengine/docs/standard/python/taskqueue) for information on how to use queues directly.

### Queues in Local Development

The App Engine Admin server can be used to view queues and enqueued tasks. Once `dev_appserver.py` is running, navigate to [http://0.0.0.0:8000/taskqueue](http://0.0.0.0:8000/taskqueue) to view queues and tasks for the local instance.

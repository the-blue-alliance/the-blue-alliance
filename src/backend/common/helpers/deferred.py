import base64
import pickle
from typing import Any, Generator

from google.appengine.api import taskqueue
from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.ext import ndb
from google.appengine.ext.deferred.deferred import (
    _curry_callable,
    _DEFAULT_QUEUE,
    _DeferredTaskEntity,
    _TASKQUEUE_HEADERS,
    run,
    run_from_datastore,
)

_DEFAULT_URL = "/_ah/queue/deferred_encoded"


def _serialize(obj: Any, *args, **kwargs) -> bytes:
    curried = _curry_callable(obj, *args, **kwargs)
    return pickle.dumps(curried, protocol=2)


@ndb.tasklet
def defer_safe_async(
    obj: Any, *args, **kwargs
) -> Generator[Any, Any, UserRPC]:
    """
    A wrapper around app enginer's deferred.defer, but will also base64 encode the payload
    Which avoids some unicode errors when passing arguments with certain types of binary properties
    """

    taskargs = dict(
        (x, kwargs.pop(("_%s" % x), None))
        for x in ("countdown", "eta", "name", "target", "retry_options")
    )
    taskargs["url"] = kwargs.pop("_url", _DEFAULT_URL)
    transactional = kwargs.pop("_transactional", False)
    taskargs["headers"] = dict(_TASKQUEUE_HEADERS)
    taskargs["headers"].update(kwargs.pop("_headers", {}))
    queue = kwargs.pop("_queue", _DEFAULT_QUEUE)
    pickled = _serialize(obj, *args, **kwargs)
    try:
        task = taskqueue.Task(payload=base64.b64encode(pickled), **taskargs)
        rpc: UserRPC = yield task.add_async(queue, transactional=transactional)
        return rpc
    except taskqueue.TaskTooLargeError:
        key = _DeferredTaskEntity(data=pickled).put()
        pickled = _serialize(run_from_datastore, str(key))
        task = taskqueue.Task(payload=base64.b64encode(pickled), **taskargs)
        rpc = yield task.add_async(queue)
        return rpc


def defer_safe(obj: Any, *args, **kwargs) -> taskqueue.Task:
    return defer_safe_async(obj, *args, **kwargs).get_result()


def run_from_task(task: taskqueue.Task) -> None:
    decoded = base64.b64decode(task.payload)
    run(decoded)

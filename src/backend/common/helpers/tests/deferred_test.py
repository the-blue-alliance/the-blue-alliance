import six
from google.appengine.ext import testbed

from backend.common.helpers.deferred import defer_safe, run_from_task


def _drain_deferred(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    tasks = taskqueue_stub.get_filtered_tasks()
    assert len(tasks) == 1

    task = tasks[0]
    six.ensure_text(task.payload)
    run_from_task(task)


def _fn(*args, **kwargs) -> None:
    pass


def test_enqueue_deferred(
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:

    arg = "\0"
    defer_safe(_fn, arg)
    _drain_deferred(taskqueue_stub)

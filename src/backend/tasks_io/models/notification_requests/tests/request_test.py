import pytest

from backend.tasks_io.models.notification_requests.request import Request
from backend.tasks_io.models.notifications.tests.mocks.notifications.mock_notification import (
    MockNotification,
)


def test_init():
    Request(MockNotification())


def test_send():
    request = Request(MockNotification())
    with pytest.raises(NotImplementedError):
        request.send()


def test_defer_track_notification(taskqueue_stub):
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="api-track-call")
    assert len(tasks) == 0

    request = Request(MockNotification())
    request.defer_track_notification(2)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="api-track-call")
    assert len(tasks) == 1

    task = tasks[0]
    assert task.url == "/_ah/queue/deferred_notification_track_send"

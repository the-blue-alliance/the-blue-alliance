from unittest import mock

from werkzeug.test import Client

from backend.common.helpers.firebase_pusher import FirebasePusher


@mock.patch.object(FirebasePusher, "update_live_events")
def test_update_live_events(update_mock: mock.Mock, tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    update_mock.assert_called_once()

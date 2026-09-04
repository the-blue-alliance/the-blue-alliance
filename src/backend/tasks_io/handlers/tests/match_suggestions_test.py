from unittest import mock

from werkzeug.test import Client

from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.match_suggestion_helper import MatchSuggestionHelper
from backend.common.models.match_suggestion import MatchSuggestions


@mock.patch.object(FirebasePusher, "update_match_suggestions")
def test_update_match_suggestions(update_mock: mock.Mock, tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/update_match_suggestions")

    assert resp.status_code == 200
    update_mock.assert_called_once()


@mock.patch.object(FirebasePusher, "update_match_suggestions")
@mock.patch.object(MatchSuggestionHelper, "compute_match_suggestions")
def test_reports_how_many_were_pushed(
    compute_mock: mock.Mock, update_mock: mock.Mock, tasks_client: Client
) -> None:
    compute_mock.return_value = MatchSuggestions(updated_at=0)

    resp = tasks_client.get("/tasks/do/update_match_suggestions")

    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "Pushed 0 match suggestions"
    update_mock.assert_called_once_with(compute_mock.return_value)


@mock.patch.object(FirebasePusher, "update_match_suggestions")
def test_stays_quiet_when_run_as_a_task(
    update_mock: mock.Mock, tasks_client: Client
) -> None:
    resp = tasks_client.get(
        "/tasks/do/update_match_suggestions",
        headers={"X-Appengine-Taskname": "some-task"},
    )

    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == ""

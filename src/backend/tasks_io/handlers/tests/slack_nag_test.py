from unittest.mock import Mock, patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)
from backend.common.models.account import Account
from backend.common.models.suggestion import Suggestion
from backend.common.sitevars.slack_hook_urls import SlackHookUrls
from backend.common.suggestions.suggestion_creator import SuggestionCreator


@patch.object(OutgoingNotificationHelper, "send_slack_alert")
def test_nag_no_sitevar(notif_mock: Mock, tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/nag_suggestions")
    assert resp.status_code == 200

    assert notif_mock.call_count == 0


@patch.object(OutgoingNotificationHelper, "send_slack_alert")
def test_nag_no_suggestions(
    notif_mock: Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    SlackHookUrls.put({"suggestion-nag": "http://foo.bar/nag"})
    resp = tasks_client.get("/tasks/do/nag_suggestions")
    assert resp.status_code == 200

    assert notif_mock.call_count == 0


def _pending(suggestion_id: str, target_model: str) -> None:
    Suggestion(
        id=suggestion_id,
        author=ndb.Key(Account, "foo@bar.com"),
        target_model=target_model,
        review_state=SuggestionState.REVIEW_PENDING,
    ).put()


@patch.object(OutgoingNotificationHelper, "send_slack_alert")
def test_nag_single_suggestion(
    notif_mock: Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    SlackHookUrls.put({"suggestion-nag": "http://foo.bar/nag"})
    _, suggestion = SuggestionCreator.createTeamMediaSuggestion(
        author_account_key=ndb.Key(Account, "foo@bar.com"),
        media_url="https://imgur.com/abc1234",
        team_key="frc254",
        year_str="2020",
    ).get_result()
    none_throws(suggestion).put()

    resp = tasks_client.get("/tasks/do/nag_suggestions")
    assert resp.status_code == 200

    assert notif_mock.call_count == 1
    channel_url, nag_text = notif_mock.call_args.args
    assert channel_url == "http://foo.bar/nag"
    assert nag_text.split("\n") == [
        "*:inbox_tray: 1 suggestion <https://beta.thebluealliance.com/suggest/review|needs review>*",
        "• <https://beta.thebluealliance.com/suggest/review/media|Team Media>: 1",
    ]


@patch.object(OutgoingNotificationHelper, "send_slack_alert")
def test_nag_totals_and_sorts_types_by_count(
    notif_mock: Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    SlackHookUrls.put({"suggestion-nag": "http://foo.bar/nag"})
    _pending("m1", "match")
    for i in range(3):
        _pending(f"a{i}", "api_auth_access")
    for i in range(2):
        _pending(f"w{i}", "event")

    resp = tasks_client.get("/tasks/do/nag_suggestions")
    assert resp.status_code == 200

    _, nag_text = notif_mock.call_args.args
    base = "https://beta.thebluealliance.com/suggest/review"
    assert nag_text.split("\n") == [
        f"*:inbox_tray: 6 suggestions <{base}|need review>*",
        f"• <{base}/api_auth_access|API Write Key Requests>: 3",
        f"• <{base}/event|Webcasts>: 2",
        f"• <{base}/match|Match Videos>: 1",
    ]
    # The Jinja review page is gone; never send moderators to www
    assert "www.thebluealliance.com" not in nag_text

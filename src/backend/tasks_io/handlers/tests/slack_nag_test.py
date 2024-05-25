from unittest.mock import Mock, patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)
from backend.common.models.account import Account
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


@patch.object(OutgoingNotificationHelper, "send_slack_alert")
def test_nag(
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
    )
    none_throws(suggestion).put()

    resp = tasks_client.get("/tasks/do/nag_suggestions")
    assert resp.status_code == 200

    assert notif_mock.call_count == 1

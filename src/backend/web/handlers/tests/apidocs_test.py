import json
from typing import List
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.client_type import ClientType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.notification_type import (
    ENABLED_NOTIFICATIONS,
    NotificationType,
)
from backend.common.consts.notification_type import TYPES as NOTIFICATION_TYPES
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.match import Match, MatchAlliance
from backend.common.models.mobile_client import MobileClient
from backend.web.handlers.conftest import CapturedTemplate


@pytest.fixture
def apidocs_event(ndb_stub) -> Event:
    e = Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=EventType.OFFSEASON,
    )
    e.put()
    return e


@pytest.fixture
def apidocs_match(apidocs_event, ndb_stub) -> Match:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(
        id="2019nyny_qm1",
        year=2019,
        match_number=1,
        set_number=1,
        event=apidocs_event.key,
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(alliance_dict),
    )
    m.put()
    return m


def test_apidocs_overview(
    web_client: Client, captured_templates: List[CapturedTemplate]
) -> None:
    resp = web_client.get("/apidocs")
    assert resp.status_code == 200
    template = captured_templates[0][0]
    assert template.name == "apidocs_overview.html"


def test_test_apidocs_trusted_redirect(web_client: Client) -> None:
    resp = web_client.get("/apidocs/trusted")
    assert resp.status_code == 302
    parsed_location = urlparse(resp.headers["Location"])
    assert parsed_location.path == "/apidocs/trusted/v1"


def test_apidocs_trusted_v1(
    web_client: Client, captured_templates: List[CapturedTemplate]
) -> None:
    resp = web_client.get("/apidocs/trusted/v1")
    assert resp.status_code == 200
    template = captured_templates[0][0]
    assert template.name == "apidocs_swagger.html"
    context = captured_templates[0][1]
    assert context["title"] == "Trusted APIv1"
    assert context["swagger_url"] == "/swagger/api_trusted_v1.json"


def test_apidocs_v3(
    web_client: Client, captured_templates: List[CapturedTemplate]
) -> None:
    resp = web_client.get("/apidocs/v3")
    assert resp.status_code == 200
    template = captured_templates[0][0]
    assert template.name == "apidocs_swagger.html"
    context = captured_templates[0][1]
    assert context["title"] == "APIv3"
    assert context["swagger_url"] == "/swagger/api_v3.json"


def test_apidocs_webhooks(
    web_client: Client, captured_templates: List[CapturedTemplate]
) -> None:
    resp = web_client.get("/apidocs/webhooks")
    assert resp.status_code == 200
    template = captured_templates[0][0]
    assert template.name == "apidocs_webhooks.html"
    context = captured_templates[0][1]
    assert context["enabled"] == ENABLED_NOTIFICATIONS
    assert context["types"] == NOTIFICATION_TYPES


def test_apidocs_webhooks_notification_logged_out(web_client: Client) -> None:
    response = web_client.post("/apidocs/webhooks/test/0")
    assert response.status_code == 401


def test_apidocs_webhooks_notification_invalid_type(
    login_user, web_client: Client
) -> None:
    response = web_client.post("/apidocs/webhooks/test/7372")
    assert response.status_code == 400


event_notification_types = [
    NotificationType.ALLIANCE_SELECTION,
    NotificationType.AWARDS,
    NotificationType.SCHEDULE_UPDATED,
]
match_notification_types = [
    NotificationType.UPCOMING_MATCH,
    NotificationType.MATCH_SCORE,
    NotificationType.LEVEL_STARTING,
    NotificationType.MATCH_VIDEO,
]


def test_apidocs_webhooks_notification_no_webhook_specified(
    login_user, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{NotificationType.MATCH_SCORE.value}",
        data={"match_key": "2019nyny_qm1"},
    )
    assert response.status_code == 400
    assert b"Webhook not specified" in response.data


# Tests for webhook-specific test notifications
@pytest.fixture
def verified_webhook(login_user, ndb_stub) -> MobileClient:
    webhook = MobileClient(
        parent=ndb.Key(Account, login_user.uid),
        user_id=str(login_user.uid),
        messaging_id="https://example.com/webhook",
        client_type=ClientType.WEBHOOK,
        secret="secret123",
        display_name="Test Webhook",
        verified=True,
    )
    webhook.put()
    return webhook


@pytest.fixture
def unverified_webhook(login_user, ndb_stub) -> MobileClient:
    webhook = MobileClient(
        parent=ndb.Key(Account, login_user.uid),
        user_id=str(login_user.uid),
        messaging_id="https://example.com/unverified",
        client_type=ClientType.WEBHOOK,
        secret="secret456",
        display_name="Unverified Webhook",
        verified=False,
    )
    webhook.put()
    return webhook


def test_apidocs_webhooks_shows_user_webhooks(
    login_user,
    verified_webhook,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.get("/apidocs/webhooks")
    assert resp.status_code == 200
    context = captured_templates[0][1]
    assert "webhooks" in context
    assert len(context["webhooks"]) == 1
    assert context["webhooks"][0].key == verified_webhook.key


def test_apidocs_webhooks_notification_with_webhook_not_found(
    login_user, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{NotificationType.MATCH_SCORE.value}",
        data={"match_key": "2019nyny_qm1", "webhook_client_id": "999999"},
    )
    assert response.status_code == 400
    assert b"Webhook not found" in response.data


def test_apidocs_webhooks_notification_with_unverified_webhook(
    login_user, unverified_webhook, apidocs_match, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{NotificationType.MATCH_SCORE.value}",
        data={
            "match_key": "2019nyny_qm1",
            "webhook_client_id": str(unverified_webhook.key.id()),
        },
    )
    assert response.status_code == 400
    assert b"not verified" in response.data


@pytest.mark.parametrize("type", event_notification_types)
def test_apidocs_webhooks_notification_event_with_webhook(
    type: NotificationType,
    apidocs_event,
    login_user,
    verified_webhook,
    web_client: Client,
) -> None:
    with patch.object(TBANSHelper, "send_webhook_test", return_value=True) as mock_send:
        response = web_client.post(
            f"/apidocs/webhooks/test/{type.value}",
            data={
                "event_key": "2019nyny",
                "webhook_client_id": str(verified_webhook.key.id()),
            },
        )
    assert response.status_code == 200
    mock_send.assert_called_once()
    # Verify it was called with the correct webhook and notification type
    call_args = mock_send.call_args
    assert call_args[0][0].key == verified_webhook.key
    assert call_args[0][1] == type
    assert call_args[1]["event_key"] == "2019nyny"
    assert call_args[1]["team_key"] is None
    assert call_args[1]["match_key"] is None
    assert call_args[1]["district_key"] is None


@pytest.mark.parametrize("type", match_notification_types)
def test_apidocs_webhooks_notification_match_with_webhook(
    type: NotificationType,
    apidocs_match,
    login_user,
    verified_webhook,
    web_client: Client,
) -> None:
    with patch.object(TBANSHelper, "send_webhook_test", return_value=True) as mock_send:
        response = web_client.post(
            f"/apidocs/webhooks/test/{type.value}",
            data={
                "match_key": "2019nyny_qm1",
                "webhook_client_id": str(verified_webhook.key.id()),
            },
        )
    assert response.status_code == 200
    mock_send.assert_called_once()
    # Verify it was called with the correct webhook and notification type
    call_args = mock_send.call_args
    assert call_args[0][0].key == verified_webhook.key
    assert call_args[0][1] == type
    assert call_args[1]["event_key"] is None
    assert call_args[1]["team_key"] is None
    assert call_args[1]["match_key"] == "2019nyny_qm1"
    assert call_args[1]["district_key"] is None


def test_apidocs_webhooks_notification_with_webhook_send_failure(
    apidocs_match, login_user, verified_webhook, web_client: Client
) -> None:
    with patch.object(
        TBANSHelper, "send_webhook_test", return_value=False
    ) as mock_send:
        response = web_client.post(
            f"/apidocs/webhooks/test/{NotificationType.MATCH_SCORE.value}",
            data={
                "match_key": "2019nyny_qm1",
                "webhook_client_id": str(verified_webhook.key.id()),
            },
        )
    assert response.status_code == 400
    assert b"Failed to send notification" in response.data
    mock_send.assert_called_once()


def test_apidocs_webhooks_notification_with_webhook_missing_match(
    login_user, verified_webhook, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{NotificationType.MATCH_SCORE.value}",
        data={
            "match_key": "nonexistent",
            "webhook_client_id": str(verified_webhook.key.id()),
        },
    )
    assert response.status_code == 400
    assert b"Failed to send notification" in response.data


def test_apidocs_webhooks_notification_with_webhook_missing_event(
    login_user, verified_webhook, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{NotificationType.AWARDS.value}",
        data={
            "event_key": "nonexistent",
            "webhook_client_id": str(verified_webhook.key.id()),
        },
    )
    assert response.status_code == 400
    assert b"Failed to send notification" in response.data


def test_apidocs_webhooks_notification_ping_no_keys_required(
    login_user, verified_webhook, web_client: Client
) -> None:
    with patch.object(TBANSHelper, "send_webhook_test", return_value=True) as mock_send:
        response = web_client.post(
            f"/apidocs/webhooks/test/{NotificationType.PING.value}",
            data={
                "webhook_client_id": str(verified_webhook.key.id()),
            },
        )
    assert response.status_code == 200
    mock_send.assert_called_once()


def test_apidocs_webhooks_notification_with_team_key(
    apidocs_event, login_user, verified_webhook, ndb_stub, web_client: Client
) -> None:
    from backend.common.models.team import Team

    team = Team(id="frc1", team_number=1)
    team.put()

    with patch.object(TBANSHelper, "send_webhook_test", return_value=True) as mock_send:
        response = web_client.post(
            f"/apidocs/webhooks/test/{NotificationType.AWARDS.value}",
            data={
                "event_key": "2019nyny",
                "team_key": "frc1",
                "webhook_client_id": str(verified_webhook.key.id()),
            },
        )
    assert response.status_code == 200
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[1]["event_key"] == "2019nyny"
    assert call_args[1]["team_key"] == "frc1"

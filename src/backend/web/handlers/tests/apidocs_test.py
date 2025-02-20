import json
from typing import List
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from werkzeug.test import Client

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.notification_type import (
    ENABLED_NOTIFICATIONS,
    NotificationType,
)
from backend.common.consts.notification_type import TYPES as NOTIFICATION_TYPES
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.models.event import Event
from backend.common.models.match import Match, MatchAlliance
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


@pytest.mark.parametrize("type", event_notification_types)
def test_apidocs_webhooks_notification_event_empty(
    type: NotificationType, login_user, web_client: Client
) -> None:
    response = web_client.post(f"/apidocs/webhooks/test/{type}")
    assert response.status_code == 400


@pytest.mark.parametrize("type", event_notification_types)
def test_apidocs_webhooks_notification_event_missing(
    type: NotificationType, login_user, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{type}", data={"event_key": "2019nyny"}
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "type, method",
    zip(event_notification_types, ["alliance_selection", "awards", "event_schedule"]),
)
def test_apidocs_webhooks_notification_event(
    type: NotificationType, method: str, apidocs_event, login_user, web_client: Client
) -> None:
    with patch.object(TBANSHelper, method) as mock_tbans_call:
        response = web_client.post(
            f"/apidocs/webhooks/test/{type.value}", data={"event_key": "2019nyny"}
        )
    assert response.status_code == 200
    mock_tbans_call.assert_called_once_with(apidocs_event, user_id=str(login_user.uid))


@pytest.mark.parametrize("type", match_notification_types)
def test_apidocs_webhooks_notification_match_empty(
    type: NotificationType, login_user, web_client: Client
) -> None:
    response = web_client.post(f"/apidocs/webhooks/test/{type}")
    assert response.status_code == 400


@pytest.mark.parametrize("type", match_notification_types)
def test_apidocs_webhooks_notification_match_missing(
    type: NotificationType, login_user, web_client: Client
) -> None:
    response = web_client.post(
        f"/apidocs/webhooks/test/{type}", data={"match_key": "2019nyny_qm1"}
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    "type, method",
    zip(
        match_notification_types,
        ["match_upcoming", "match_score", "event_level", "match_video"],
    ),
)
def test_apidocs_webhooks_notification_match(
    type: NotificationType, method: str, apidocs_match, login_user, web_client: Client
) -> None:
    with patch.object(TBANSHelper, method) as mock_tbans_call:
        response = web_client.post(
            f"/apidocs/webhooks/test/{type.value}", data={"match_key": "2019nyny_qm1"}
        )
    assert response.status_code == 200
    mock_tbans_call.assert_called_once_with(apidocs_match, user_id=str(login_user.uid))

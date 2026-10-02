from datetime import datetime
from typing import cast

import pytest
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.sitevars import apistatus
from backend.common.sitevars.apistatus import ApiStatus
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown


@pytest.mark.parametrize("fmsapi_down", [True, False])
def test_status(fmsapi_down, ndb_stub, api_client: Client) -> None:
    status = apistatus.ContentType(
        current_season=2019,
        max_season=2020,
        web=None,
        android=None,
        ios=None,
        max_team_page=0,
    )

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    Team(
        id="frc1",
        team_number=1,
    ).put()

    ApiStatus.put(status)
    ApiStatusFMSApiDown.put(fmsapi_down)

    resp = api_client.get("/api/v3/status", headers={"X-TBA-Auth-Key": "test_auth_key"})
    assert resp.status_code == 200

    expected_status = dict()
    expected_status.update(cast(dict, status))
    expected_status["down_events"] = []
    expected_status["is_datafeed_down"] = fmsapi_down
    expected_status["kickoff_datetime"] = resp.json["kickoff_datetime"]

    assert resp.json == expected_status


@pytest.mark.parametrize(
    "now, expected_kickoff_year",
    [
        ("2026-02-01", 2026),
        ("2026-09-02", 2027),
    ],
)
def test_status_kickoff_datetime(
    now, expected_kickoff_year, ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    Team(
        id="frc1",
        team_number=1,
    ).put()

    # The last official event of the 2026 season, so kickoff rolls to 2027 only
    # once it has been played
    Event(
        id="2026test",
        event_short="test",
        start_date=datetime(2026, 4, 1),
        end_date=datetime(2026, 4, 30),
        event_type_enum=EventType.REGIONAL,
        year=2026,
    ).put()

    with freeze_time(now):
        resp = api_client.get(
            "/api/v3/status", headers={"X-TBA-Auth-Key": "test_auth_key"}
        )

    assert resp.status_code == 200
    assert (
        resp.json["kickoff_datetime"]
        == SeasonHelper.kickoff_datetime_utc(expected_kickoff_year).isoformat()
    )

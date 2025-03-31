from typing import cast

import pytest
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
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

    assert resp.json == expected_status

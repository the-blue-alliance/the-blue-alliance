from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District


def test_district_list_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
    ).put()

    # Test empty year
    resp = api_client.get(
        "/api/v3/districts/2019", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json == []

    # Test non-empty year
    resp = api_client.get(
        "/api/v3/districts/2020", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    district_keys = set([d["key"] for d in resp.json])
    assert "2020ne" in district_keys
    assert "2020fim" in district_keys

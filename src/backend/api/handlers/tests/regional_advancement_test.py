from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.models.regional_pool_ranking import RegionalPoolRanking


def test_regional_rankings_no_auth(ndb_stub, api_client: Client) -> None:
    resp = api_client.get(
        "/api/v3/regional_advancement/2020/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 401


def test_regional_rankings_bad_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    resp = api_client.get(
        "/api/v3/regional_advancement/2020/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404


def test_regional_rankings_no_pool_model(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    resp = api_client.get(
        "/api/v3/regional_advancement/2025/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404


def test_regional_rankings_empty(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    pool = RegionalChampsPool(
        id="2025",
        year=2020,
    )
    pool.put()

    resp = api_client.get(
        "/api/v3/regional_advancement/2025/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json is None


def test_regional_rankings(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    rankings = [
        RegionalPoolRanking(
            rank=13,
            team_key="frc604",
            point_total=50,
            rookie_bonus=5,
            single_event_bonus=0,
            event_points=[],
        )
    ]
    pool = RegionalChampsPool(
        id="2025",
        year=2020,
        rankings=rankings,
    )
    pool.put()

    resp = api_client.get(
        "/api/v3/regional_advancement/2025/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == rankings

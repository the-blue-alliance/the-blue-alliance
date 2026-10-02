from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    RegionalPoolAdvancement,
    TeamRegionalPoolAdvancement,
)
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


def test_regional_advancement_no_auth(ndb_stub, api_client: Client) -> None:
    resp = api_client.get(
        "/api/v3/regional_advancement/2025",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 401


def test_regional_advancement_bad_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    resp = api_client.get(
        "/api/v3/regional_advancement/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404
    assert resp.json == {"Error": "2020 is not a valid year for regional advancement"}


def test_regional_advancement_no_pool_model(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    resp = api_client.get(
        "/api/v3/regional_advancement/2025",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404
    assert resp.json == {"Error": "No regional advancement found for 2025"}


def test_regional_advancement_empty(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    RegionalChampsPool(id="2025", year=2025).put()

    resp = api_client.get(
        "/api/v3/regional_advancement/2025",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json is None


def test_regional_advancement(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    advancement: RegionalPoolAdvancement = {
        "frc604": TeamRegionalPoolAdvancement(
            cmp=True,
            cmp_status=ChampionshipStatus.EVENT_QUALIFIED,
            qualifying_event="2025casj",
            qualifying_award_name="Regional Winners",
        ),
        "frc254": TeamRegionalPoolAdvancement(
            cmp=True,
            cmp_status=ChampionshipStatus.POOL_QUALIFIED,
            qualifying_pool_week=3,
        ),
        "frc1": TeamRegionalPoolAdvancement(
            cmp=False,
            cmp_status=ChampionshipStatus.NOT_INVITED,
        ),
    }
    RegionalChampsPool(id="2025", year=2025, advancement=advancement).put()

    resp = api_client.get(
        "/api/v3/regional_advancement/2025",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == {
        "frc604": {
            "cmp": True,
            "cmp_status": "EventQualified",
            "qualifying_event": "2025casj",
            "qualifying_award_name": "Regional Winners",
        },
        "frc254": {
            "cmp": True,
            "cmp_status": "PoolQualified",
            "qualifying_pool_week": 3,
        },
        "frc1": {"cmp": False, "cmp_status": "NotInvited"},
    }

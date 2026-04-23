from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.insight_v2 import InsightCategory, InsightV2


def _put_auth(key: str = "test_auth_key") -> None:
    ApiAuthAccess(
        id=key,
        auth_types_enum=[AuthType.READ_API],
    ).put()


def _put_insight(
    year: int,
    name: str = "blue_banners",
    district_abbreviation: str | None = None,
) -> InsightV2:
    data = {
        "key_type": "team",
        "rankings": [{"keys": ["frc1"], "value": 3}],
    }
    insight = InsightV2(
        id=InsightV2.render_key_name(
            year, InsightCategory.LEADERBOARD, name, district_abbreviation
        ),
        name=name,
        display_name="Total Blue Banners",
        year=year,
        category=InsightCategory.LEADERBOARD,
        data_json=data,
        district_abbreviation=district_abbreviation,
    )
    insight.put()
    return insight


def test_insights_v2_year_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/v2/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_v2_year(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)

    resp = api_client.get(
        "/api/v3/insights/v2/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    result = resp.json[0]
    assert result["name"] == "blue_banners"
    assert result["display_name"] == "Total Blue Banners"
    assert result["year"] == 2024
    assert result["category"] == InsightCategory.LEADERBOARD
    assert result["data"]["key_type"] == "team"


def test_insights_v2_year_does_not_return_other_years(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    _put_insight(2024)
    _put_insight(2023)

    resp = api_client.get(
        "/api/v3/insights/v2/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["year"] == 2024


def test_insights_v2_year_category(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)

    resp = api_client.get(
        f"/api/v3/insights/v2/2024/{InsightCategory.LEADERBOARD}",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["category"] == InsightCategory.LEADERBOARD


def test_insights_v2_year_category_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)

    resp = api_client.get(
        "/api/v3/insights/v2/2024/streak",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_v2_year_no_district(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)

    resp = api_client.get(
        "/api/v3/insights/v2/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json[0]["district_abbreviation"] is None


def test_insights_v2_year_with_district(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024, district_abbreviation="ne")

    resp = api_client.get(
        "/api/v3/insights/v2/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json[0]["district_abbreviation"] == "ne"


def test_insights_v2_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/insights/v2/2024")
    assert resp.status_code == 401

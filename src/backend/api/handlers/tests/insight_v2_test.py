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
    category: str = InsightCategory.LEADERBOARD,
    display_name: str = "Total Blue Banners",
) -> InsightV2:
    data = {
        "key_type": "team",
        "context_type": "none",
        "rankings": [{"keys": ["frc1"], "value": 3}],
    }
    insight = InsightV2(
        id=InsightV2.render_key_name(year, category, name, district_abbreviation),
        name=name,
        display_name=display_name,
        year=year,
        category=category,
        data_json=data,
        district_abbreviation=district_abbreviation,
    )
    insight.put()
    return insight


# ---------------------------------------------------------------------------
# Official route: GET /api/v3/insights/{year}
# ---------------------------------------------------------------------------


def test_insights_year_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_year_returns_global(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)

    resp = api_client.get(
        "/api/v3/insights/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["district_abbreviation"] is None


def test_insights_year_excludes_district(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)
    _put_insight(2024, name="blue_banners_ne", district_abbreviation="ne")

    resp = api_client.get(
        "/api/v3/insights/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["district_abbreviation"] is None


def test_insights_year_filter(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024)
    _put_insight(2023)

    resp = api_client.get(
        "/api/v3/insights/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["year"] == 2024


def test_insights_year_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/insights/2024")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Official route: GET /api/v3/insights/{year}/{category}
# ---------------------------------------------------------------------------


def test_insights_year_category_filters(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024, name="blue_banners", category=InsightCategory.LEADERBOARD)
    _put_insight(2024, name="win_streak", category=InsightCategory.STREAK)

    resp = api_client.get(
        "/api/v3/insights/2024/leaderboard",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["category"] == InsightCategory.LEADERBOARD


def test_insights_year_category_excludes_district(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024, name="blue_banners", category=InsightCategory.LEADERBOARD)
    _put_insight(
        2024,
        name="blue_banners_ne",
        category=InsightCategory.LEADERBOARD,
        district_abbreviation="ne",
    )

    resp = api_client.get(
        "/api/v3/insights/2024/leaderboard",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["district_abbreviation"] is None


def test_insights_year_category_invalid_returns_404(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024/club",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404


def test_insights_year_category_unknown_returns_404(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024/notarealcategory",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404


def test_insights_year_category_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/insights/2024/leaderboard")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Official route: GET /api/v3/insights/{year}/district/{district_abbreviation}
# ---------------------------------------------------------------------------


def test_insights_year_district_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_year_district_returns_only_that_district(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    _put_insight(2024)  # global — should be excluded
    _put_insight(2024, name="blue_banners_ne", district_abbreviation="ne")
    _put_insight(2024, name="blue_banners_fim", district_abbreviation="fim")

    resp = api_client.get(
        "/api/v3/insights/2024/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["district_abbreviation"] == "ne"


def test_insights_year_district_no_match_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2024, name="blue_banners_ne", district_abbreviation="ne")

    resp = api_client.get(
        "/api/v3/insights/2024/district/fim",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_year_district_year_filter(ndb_stub, api_client: Client) -> None:
    _put_auth()
    _put_insight(2023, name="blue_banners_ne", district_abbreviation="ne")

    resp = api_client.get(
        "/api/v3/insights/2024/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_year_district_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/insights/2024/district/ne")
    assert resp.status_code == 401


def test_insights_year_district_literal_does_not_collide(
    ndb_stub, api_client: Client
) -> None:
    """Confirm /insights/{year}/district/{abbrev} resolves to the district handler,
    not the category handler with category='district'."""
    _put_auth()
    _put_insight(2024, name="blue_banners_ne", district_abbreviation="ne")

    resp = api_client.get(
        "/api/v3/insights/2024/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["district_abbreviation"] == "ne"


# ---------------------------------------------------------------------------
# Official route: GET /api/v3/insights/{year}/{category}/district/{district_abbreviation}
# ---------------------------------------------------------------------------


def test_insights_year_category_district_empty(ndb_stub, api_client: Client) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024/leaderboard/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_year_category_district_filters_both(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    _put_insight(
        2024,
        name="blue_banners_ne",
        category=InsightCategory.LEADERBOARD,
        district_abbreviation="ne",
    )
    _put_insight(
        2024,
        name="win_streak_ne",
        category=InsightCategory.STREAK,
        district_abbreviation="ne",
    )
    _put_insight(
        2024,
        name="blue_banners_fim",
        category=InsightCategory.LEADERBOARD,
        district_abbreviation="fim",
    )
    _put_insight(2024, name="blue_banners")  # global

    resp = api_client.get(
        "/api/v3/insights/2024/leaderboard/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    result = resp.json[0]
    assert result["category"] == InsightCategory.LEADERBOARD
    assert result["district_abbreviation"] == "ne"


def test_insights_year_category_district_invalid_category_404(
    ndb_stub, api_client: Client
) -> None:
    _put_auth()
    resp = api_client.get(
        "/api/v3/insights/2024/club/district/ne",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404


def test_insights_year_category_district_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/insights/2024/leaderboard/district/ne")
    assert resp.status_code == 401

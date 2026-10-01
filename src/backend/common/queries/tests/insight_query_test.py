import json

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.insight import Insight
from backend.common.queries.insight_query import (
    DistrictInsightsYearQuery,
    InsightsLeaderboardsYearQuery,
    InsightsNotablesYearQuery,
)


def _insight(
    insight_type: int, year: int, district_abbreviation: str | None = None
) -> Insight:
    name = Insight.INSIGHT_NAMES[insight_type]
    insight = Insight(
        id=Insight.render_key_name(year, name, district_abbreviation),
        name=name,
        year=year,
        data_json=json.dumps({"value": insight_type}),
        district_abbreviation=district_abbreviation,
    )
    insight.put()
    return insight


def test_leaderboards_year_query() -> None:
    leaderboard = _insight(Insight.TYPED_LEADERBOARD_BLUE_BANNERS, 2024)
    _insight(Insight.TYPED_LEADERBOARD_BLUE_BANNERS, 2023)
    _insight(Insight.MATCH_HIGHSCORE, 2024)

    assert InsightsLeaderboardsYearQuery(year=2024).fetch() == [leaderboard]
    assert InsightsLeaderboardsYearQuery(year=2024).fetch_dict(
        ApiMajorVersion.API_V3
    ) == [
        {
            "name": leaderboard.name,
            "data": {"value": Insight.TYPED_LEADERBOARD_BLUE_BANNERS},
            "year": 2024,
        }
    ]


def test_notables_year_query() -> None:
    notable = _insight(Insight.TYPED_NOTABLES_HALL_OF_FAME, 2024)
    _insight(Insight.TYPED_LEADERBOARD_BLUE_BANNERS, 2024)

    assert InsightsNotablesYearQuery(year=2024).fetch() == [notable]


def test_district_insights_year_query() -> None:
    a = _insight(Insight.TYPED_LEADERBOARD_BLUE_BANNERS, 2024, "ne")
    b = _insight(Insight.TYPED_NOTABLES_HALL_OF_FAME, 2024, "ne")
    _insight(Insight.TYPED_NOTABLES_HALL_OF_FAME, 2023, "ne")
    _insight(Insight.TYPED_NOTABLES_HALL_OF_FAME, 2024)

    result = DistrictInsightsYearQuery(district_abbreviation="ne", year=2024).fetch()
    assert sorted(i.key_name for i in result) == sorted([a.key_name, b.key_name])

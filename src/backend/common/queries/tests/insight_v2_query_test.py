from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.insight_v2 import InsightV2
from backend.common.queries.insight_v2_query import (
    InsightV2YearCategoryDistrictQuery,
    InsightV2YearCategoryQuery,
    InsightV2YearDistrictQuery,
    InsightV2YearQuery,
)


def _insight(
    name: str, year: int, category: str, district_abbreviation: str | None = None
) -> InsightV2:
    insight = InsightV2(
        id=InsightV2.render_key_name(year, category, name, district_abbreviation),
        name=name,
        display_name=name.title(),
        year=year,
        category=category,
        data_json={"name": name},
        district_abbreviation=district_abbreviation,
    )
    insight.put()
    return insight


def _names(insights: list[InsightV2]) -> list[str]:
    return sorted(i.key_name for i in insights)


def test_year_query() -> None:
    a = _insight("a", 2024, "leaderboard")
    b = _insight("b", 2024, "streak")
    _insight("c", 2024, "leaderboard", "ne")
    _insight("d", 2023, "leaderboard")

    assert _names(InsightV2YearQuery(year=2024).fetch()) == _names([a, b])
    assert InsightV2YearQuery(year=2024).fetch_dict(ApiMajorVersion.API_V3) == [
        {
            "name": i.name,
            "display_name": i.display_name,
            "year": 2024,
            "category": i.category,
            "district_abbreviation": None,
            "data": {"name": i.name},
        }
        for i in InsightV2YearQuery(year=2024).fetch()
    ]


def test_year_category_query() -> None:
    a = _insight("a", 2024, "leaderboard")
    _insight("b", 2024, "streak")
    _insight("c", 2024, "leaderboard", "ne")

    assert _names(
        InsightV2YearCategoryQuery(year=2024, category="leaderboard").fetch()
    ) == _names([a])


def test_year_district_query() -> None:
    a = _insight("a", 2024, "leaderboard", "ne")
    b = _insight("b", 2024, "streak", "ne")
    _insight("c", 2024, "leaderboard")
    _insight("d", 2024, "leaderboard", "fim")

    assert _names(
        InsightV2YearDistrictQuery(year=2024, district_abbreviation="ne").fetch()
    ) == _names([a, b])


def test_year_category_district_query() -> None:
    a = _insight("a", 2024, "leaderboard", "ne")
    _insight("b", 2024, "streak", "ne")
    _insight("c", 2024, "leaderboard")

    assert _names(
        InsightV2YearCategoryDistrictQuery(
            year=2024, category="leaderboard", district_abbreviation="ne"
        ).fetch()
    ) == _names([a])

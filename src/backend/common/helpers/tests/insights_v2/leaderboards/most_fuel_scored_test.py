from backend.common.helpers.insights_v2.leaderboards.most_fuel_scored import (
    MostFuelScored2026V2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year


def test_most_fuel_scored_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2026marea.json")
    test_data_importer.import_match_list(__file__, "../../data/2026marea_matches.json")

    insights = compute_insights_for_year(2026, [MostFuelScored2026V2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "most_fuel_scored"
    assert insight.display_name == "Most Fuel Scored"
    assert insight.key_name == "2026_v2_leaderboard_most_fuel_scored"


def test_most_fuel_scored_context_type(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2026marea.json")
    test_data_importer.import_match_list(__file__, "../../data/2026marea_matches.json")

    insights = compute_insights_for_year(2026, [MostFuelScored2026V2Calculator()])

    assert insights[0].data["context_type"] == "match_alliance"
    assert insights[0].data["key_type"] == "match"


def test_most_fuel_scored_top_entry(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2026marea.json")
    test_data_importer.import_match_list(__file__, "../../data/2026marea_matches.json")

    insights = compute_insights_for_year(2026, [MostFuelScored2026V2Calculator()])

    # sf1m1: red hubScore.totalCount=454
    top = insights[0].data["rankings"][0]
    assert top["value"] == 454
    assert top["keys"] == ["2026marea_sf1m1"]
    ctx = top["contexts"][0]
    assert ctx["match_key"] == "2026marea_sf1m1"
    assert set(ctx["alliance"]) == {"frc125", "frc3958", "frc5813"}


def test_most_fuel_scored_skips_year_zero(ndb_stub, test_data_importer) -> None:
    insights = compute_insights_for_year(0, [MostFuelScored2026V2Calculator()])

    assert insights == []


def test_most_fuel_scored_skips_other_years(ndb_stub, test_data_importer) -> None:
    # 2025 matches have no hubScore field
    test_data_importer.import_event(__file__, "../../data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "../../data/2025isde1_matches.json")

    insights = compute_insights_for_year(2025, [MostFuelScored2026V2Calculator()])

    assert insights == []


def test_most_fuel_scored_rankings_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../../data/2026marea.json")
    test_data_importer.import_match_list(__file__, "../../data/2026marea_matches.json")

    insights = compute_insights_for_year(2026, [MostFuelScored2026V2Calculator()])

    values = [r["value"] for r in insights[0].data["rankings"]]
    assert values == sorted(values, reverse=True)

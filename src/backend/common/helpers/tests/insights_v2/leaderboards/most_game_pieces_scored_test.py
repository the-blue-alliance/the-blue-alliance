import pytest

from backend.common.helpers.insights_v2.leaderboards.most_game_pieces_scored import (
    MostGamePiecesScoredV2Calculator,
)
from backend.common.helpers.insights_v2.registry import compute_insights_for_year

# (year, event_key, expected display_name, expected top value, possible top match keys)
# Top values/keys computed directly from the fixture data; several years have
# multiple matches tied for the top count (grouped into one ranking entry).
CASES = [
    (2016, "2016nyny", "Most Boulders Scored", 9, {"2016nyny_sf2m2"}),
    (2017, "2017nyny", "Most Fuel Scored", 119, {"2017nyny_qm1"}),
    (
        2019,
        "2019nyny",
        "Most Game Pieces Scored",
        22,
        {"2019nyny_qf1m2"},
    ),
    (2020, "2020scmb", "Most Power Cells Scored", 53, {"2020scmb_sf1m1"}),
    (2022, "2022cmptx", "Most Cargo Scored", 53, {"2022cmptx_sf1m12"}),
    (
        2023,
        "2023onlon",
        "Most Game Pieces Scored",
        23,
        {"2023onlon_qm19", "2023onlon_sf1m1"},
    ),
    (
        2024,
        "2024necmp",
        "Most Notes Scored",
        23,
        {
            "2024necmp_f1m1",
            "2024necmp_f1m2",
            "2024necmp_f1m3",
            "2024necmp_f1m4",
        },
    ),
    (2025, "2025isde1", "Most Coral Scored", 38, {"2025isde1_sf1m1"}),
    (2026, "2026marea", "Most Fuel Scored", 454, {"2026marea_sf1m1"}),
]


@pytest.mark.parametrize(
    "year, event_key, expected_display_name, expected_value, expected_top_keys", CASES
)
def test_most_game_pieces_scored(
    ndb_stub,
    test_data_importer,
    year,
    event_key,
    expected_display_name,
    expected_value,
    expected_top_keys,
) -> None:
    test_data_importer.import_event(__file__, f"../../data/{event_key}.json")
    test_data_importer.import_match_list(
        __file__, f"../../data/{event_key}_matches.json"
    )

    insights = compute_insights_for_year(year, [MostGamePiecesScoredV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "most_game_pieces_scored"
    assert insight.display_name == expected_display_name
    assert insight.key_name == f"{year}_v2_leaderboard_most_game_pieces_scored"
    assert insight.data["context_type"] == "match_alliance"
    assert insight.data["key_type"] == "match"

    top = insight.data["rankings"][0]
    assert top["value"] == expected_value
    assert set(top["keys"]) == expected_top_keys

    values = [r["value"] for r in insight.data["rankings"]]
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize(
    "year, event_key, expected_display_name, expected_value, expected_top_keys", CASES
)
def test_most_game_pieces_scored_skips_year_zero(
    ndb_stub,
    test_data_importer,
    year,
    event_key,
    expected_display_name,
    expected_value,
    expected_top_keys,
) -> None:
    test_data_importer.import_event(__file__, f"../../data/{event_key}.json")
    test_data_importer.import_match_list(
        __file__, f"../../data/{event_key}_matches.json"
    )

    insights = compute_insights_for_year(0, [MostGamePiecesScoredV2Calculator()])

    assert insights == []


def test_most_game_pieces_scored_skips_unsupported_year(
    ndb_stub, test_data_importer
) -> None:
    # 2018 (Power Up) has no game-piece breakdown fields recognized by this
    # calculator, so it should produce no insight even with match data present.
    test_data_importer.import_event(__file__, "../../data/2018nyny.json")
    test_data_importer.import_match_list(__file__, "../../data/2018nyny_matches.json")

    insights = compute_insights_for_year(2018, [MostGamePiecesScoredV2Calculator()])

    assert insights == []

import json
import os
from typing import Dict

import pytest

from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.models.event_matchstats import EventComponentOPRs
from backend.common.models.keys import TeamKey
from backend.common.models.stats import EventMatchStats, StatType


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def api_data_to_matchstats(
    api_data: Dict[StatType, Dict[TeamKey, float]],
) -> EventMatchStats:
    data: EventMatchStats = {}
    for stat_type in StatType:
        data[stat_type] = {
            team_key[3:]: stat for team_key, stat in api_data[stat_type].items()
        }
    return data


def assert_stats_equal(stats: EventMatchStats, expected_stats: EventMatchStats) -> None:
    assert stats.keys() == expected_stats.keys()
    for stat, team_stats in stats.items():
        assert team_stats.keys() == expected_stats[stat].keys()


def assert_coprs_keys_equal(
    coprs: EventComponentOPRs, expected_coprs: EventComponentOPRs
) -> None:
    assert coprs.keys() == expected_coprs.keys()
    for component, oprs in coprs.items():
        assert oprs.keys() == expected_coprs[component].keys()


def assert_coprs_values_equal(
    coprs: EventComponentOPRs, expected_coprs: EventComponentOPRs
) -> None:
    assert coprs.keys() == expected_coprs.keys()
    for component, oprs in coprs.items():
        assert oprs.keys() == expected_coprs[component].keys()
        for team_key, opr in oprs.items():
            assert opr == pytest.approx(  # pyre-ignore[16]
                expected_coprs[component][team_key]
            )


def test_compute_matchstats_no_matches() -> None:
    stats = MatchstatsHelper.calculate_matchstats([], 2019)
    assert stats == {}


def test_compute_matchstats(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019nyny_stats.json"), "r"
    ) as f:
        expected_stats = json.load(f)

    stats = MatchstatsHelper.calculate_matchstats(matches, 2019)
    expected_stats = api_data_to_matchstats(expected_stats)
    assert_stats_equal(stats, expected_stats)


def test_compute_matchstats_with_b_teams(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019mttd_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019mttd_stats.json"), "r"
    ) as f:
        expected_stats = json.load(f)

    stats = MatchstatsHelper.calculate_matchstats(matches, 2019)
    expected_stats = api_data_to_matchstats(expected_stats)
    assert_stats_equal(stats, expected_stats)


def test_compute_coprs_no_matches() -> None:
    stats = MatchstatsHelper.calculate_coprs([], 2022)
    assert stats == {}


def test_compute_coprs(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019nyny_coprs.json"), "r"
    ) as f:
        expected_coprs = json.load(f)

    coprs = MatchstatsHelper.calculate_coprs(matches, 2019)
    assert_coprs_keys_equal(coprs, expected_coprs)


def test_compute_coprs_2023(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2023cada_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2023cada_coprs.json"), "r"
    ) as f:
        expected_coprs = json.load(f)

    coprs = MatchstatsHelper.calculate_coprs(matches, 2023)
    assert_coprs_keys_equal(coprs, expected_coprs)
    assert_coprs_values_equal(coprs, expected_coprs)


def test_compute_coprs_with_b_teams(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019mttd_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019mttd_coprs.json"), "r"
    ) as f:
        expected_coprs = json.load(f)

    coprs = MatchstatsHelper.calculate_coprs(matches, 2019)
    assert_coprs_keys_equal(coprs, expected_coprs)

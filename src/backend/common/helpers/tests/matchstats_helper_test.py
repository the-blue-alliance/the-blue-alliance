import json
import os
from typing import Dict

import pytest

from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.models.keys import TeamKey
from backend.common.models.event_matchstats import EventMatchstats, StatType


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def api_data_to_matchstats(
    api_data: Dict[StatType, Dict[TeamKey, float]]
) -> EventMatchstats:
    data: EventMatchstats = EventMatchstats(oprs={}, dprs={}, ccwms={}, coprs={})
    for stat_type in StatType:
        data[stat_type] = {
            team_key[3:]: stat for team_key, stat in api_data[stat_type].items()
        }
    return data


def assert_stats_equal(stats: EventMatchstats, expected_stats: EventMatchstats) -> None:
    assert stats.keys() == expected_stats.keys()
    for stat, team_stats in stats.items():
        assert team_stats.keys() == expected_stats[stat].keys()


def test_compute_matchstats_no_matches() -> None:
    stats = MatchstatsHelper.calculate_matchstats([])
    assert stats == {"oprs": {}, "dprs": {}, "ccwms": {}, "coprs": {}}


def test_compute_matchstats(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019nyny_stats.json"), "r"
    ) as f:
        expected_stats = json.load(f)

    stats = MatchstatsHelper.calculate_matchstats(matches, keyed=False)
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

    stats = MatchstatsHelper.calculate_matchstats(matches, keyed=False)
    expected_stats = api_data_to_matchstats(expected_stats)
    assert_stats_equal(stats, expected_stats)


def test_compute_matchstats_skip_coprs(test_data_importer):
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019nyny_stats.json"), "r"
    ) as f:
        expected_stats = json.load(f)

    stats = MatchstatsHelper.calculate_matchstats(matches, skip_coprs=True, keyed=False)
    for stat in expected_stats.keys():
        assert expected_stats[stat] == pytest.approx(stats[stat])


def test_compute_matchstats_with_b_teams_skip_coprs(test_data_importer):
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019mttd_matches.json"
    )
    with open(
        os.path.join(os.path.dirname(__file__), "data/2019mttd_stats.json"), "r"
    ) as f:
        expected_stats = json.load(f)

    stats = MatchstatsHelper.calculate_matchstats(matches)
    for stat in expected_stats.keys():
        assert expected_stats[stat] == pytest.approx(stats[stat])

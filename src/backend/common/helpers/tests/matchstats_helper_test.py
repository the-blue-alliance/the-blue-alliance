import datetime
import json
import os
from typing import Dict, Optional

import pytest
from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_matchstats import EventComponentOPRs
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import TeamKey
from backend.common.models.match import Match
from backend.common.models.stats import EventMatchStats, StatType
from backend.common.models.team import Team


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


def _playoff_match(score_breakdown: bool) -> Match:
    return Match(
        id="2014nyny_sf1m1",
        event=ndb.Key(Event, "2014nyny"),
        year=2014,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 10},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 5},
            }
        ),
        score_breakdown_json=(
            json.dumps({"red": {"totalPoints": 10}, "blue": {"totalPoints": 5}})
            if score_breakdown
            else None
        ),
    )


def test_compute_matchstats_playoffs_only() -> None:
    assert MatchstatsHelper.calculate_matchstats([_playoff_match(False)], 2014) == {}


def test_compute_coprs_playoffs_only() -> None:
    assert MatchstatsHelper.calculate_coprs([_playoff_match(True)], 2014) == {}


def test_get_last_event_stats(memcache_stub) -> None:
    def put_event(
        event_key: str,
        start: datetime.datetime,
        event_type: EventType = EventType.REGIONAL,
        official: bool = True,
        oprs: Optional[Dict[str, float]] = None,
    ) -> None:
        Event(
            id=event_key,
            year=2020,
            event_short=event_key[4:],
            event_type_enum=event_type,
            official=official,
            start_date=start,
            end_date=start + datetime.timedelta(days=2),
        ).put()
        EventTeam(
            id=f"{event_key}_frc254",
            event=ndb.Key(Event, event_key),
            team=ndb.Key(Team, "frc254"),
            year=2020,
        ).put()
        if oprs is not None:
            EventDetails(id=event_key, matchstats={StatType.OPR: oprs}).put()

    put_event("2020nyny", datetime.datetime(2020, 3, 20))
    put_event("2020ctha", datetime.datetime(2020, 3, 1), oprs={"254": 10.0})
    put_event("2020miket", datetime.datetime(2020, 3, 8), oprs={"254": 20.0})
    put_event("2020mitry", datetime.datetime(2020, 3, 5), oprs={"254": 15.0})
    put_event(
        "2020cmptx",
        datetime.datetime(2020, 3, 10),
        event_type=EventType.CMP_FINALS,
        oprs={"254": 99.0},
    )
    put_event(
        "2020offs",
        datetime.datetime(2020, 3, 12),
        event_type=EventType.OFFSEASON,
        official=False,
        oprs={"254": 99.0},
    )

    event_key = ndb.Key(Event, "2020nyny")
    stats = MatchstatsHelper.get_last_event_stats(["254", "1124"], event_key)
    assert stats == {StatType.OPR: {"254": 20.0}}

    # The second call reuses the cached stats for 254
    stats = MatchstatsHelper.get_last_event_stats(["254"], event_key)
    assert stats == {StatType.OPR: {"254": 20.0}}

import datetime
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
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


SCHEDULE = [
    (["frc1", "frc2", "frc3"], ["frc4", "frc5", "frc6"]),
    (["frc1", "frc4", "frc5"], ["frc2", "frc3", "frc6"]),
    (["frc1", "frc2", "frc6"], ["frc3", "frc4", "frc5"]),
    (["frc2", "frc4", "frc6"], ["frc1", "frc3", "frc5"]),
]


def _qual_match(
    year: int,
    number: int,
    red: List[str],
    blue: List[str],
    red_breakdown: Dict[str, Any],
    blue_breakdown: Dict[str, Any],
) -> Match:
    return Match(
        id=f"{year}test_qm{number}",
        event=ndb.Key(Event, f"{year}test"),
        year=year,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=number,
        alliances_json=json.dumps(
            {
                "red": {"teams": red, "score": red_breakdown["totalPoints"]},
                "blue": {"teams": blue, "score": blue_breakdown["totalPoints"]},
            }
        ),
        score_breakdown_json=json.dumps({"red": red_breakdown, "blue": blue_breakdown}),
    )


def test_compute_coprs_constant_component_splits_evenly() -> None:
    matches = [
        _qual_match(2021, i, red, blue, {"totalPoints": 30}, {"totalPoints": 30})
        for i, (red, blue) in enumerate(SCHEDULE, start=1)
    ]

    coprs = MatchstatsHelper.calculate_coprs(matches, 2021)

    for team in ["1", "2", "3", "4", "5", "6"]:
        assert coprs["totalPoints"][team] == pytest.approx(10)  # pyre-ignore[16]


def test_compute_coprs_shrinks_low_sample_team_but_opr_does_not() -> None:
    schedule = SCHEDULE + [(["frc7", "frc1", "frc2"], ["frc3", "frc4", "frc5"])]
    scores = [(30, 30)] * len(SCHEDULE) + [(90, 30)]
    matches = [
        _qual_match(2021, i, red, blue, {"totalPoints": r}, {"totalPoints": b})
        for i, ((red, blue), (r, b)) in enumerate(zip(schedule, scores), start=1)
    ]

    coprs = MatchstatsHelper.calculate_coprs(matches, 2021)
    oprs = MatchstatsHelper.calculate_matchstats(matches, 2021)[StatType.OPR]

    teams = sorted({t[3:] for red, blue in schedule for t in red + blue})
    design = np.array(
        [
            [float(f"frc{t}" in alliance) for t in teams]
            for m in schedule
            for alliance in m
        ]
    )
    alliance_scores = np.array([float(s) for pair in scores for s in pair])
    least_squares = dict(
        zip(teams, np.linalg.lstsq(design, alliance_scores, rcond=None)[0])
    )
    team_mean = np.mean(alliance_scores) / 3

    assert team_mean < coprs["totalPoints"]["7"] < least_squares["7"]
    for team in teams:
        assert oprs[team] == pytest.approx(least_squares[team])  # pyre-ignore[16]


def test_compute_coprs_components_still_sum_to_total(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2023cada_matches.json"
    )

    coprs = MatchstatsHelper.calculate_coprs(matches, 2023)

    for team, total in coprs["totalPoints"].items():
        assert coprs["Total Points Less Fouls"][team] + coprs["foulPoints"][
            team
        ] == pytest.approx(  # pyre-ignore[16]
            total
        )


def _tower_breakdown(teams: List[str], climber: str) -> Dict[str, Any]:
    breakdown: Dict[str, Any] = {"totalPoints": 0, "hubScore": {}}
    for robot, team in enumerate(teams, start=1):
        breakdown[f"endGameTowerRobot{robot}"] = "Level3" if team == climber else "None"
    return breakdown


def _tower_matches(schedule: List[Tuple[List[str], List[str]]]) -> List[Match]:
    return [
        _qual_match(
            2026,
            i,
            red,
            blue,
            _tower_breakdown(red, "frc1"),
            _tower_breakdown(blue, "frc1"),
        )
        for i, (red, blue) in enumerate(schedule, start=1)
    ]


def test_compute_coprs_per_robot_follows_station_order() -> None:
    coprs = MatchstatsHelper.calculate_coprs(_tower_matches(SCHEDULE), 2026)

    assert coprs["endGameTowerPoints"]["1"] == pytest.approx(  # pyre-ignore[16]
        (120 + 4 * 5) / (4 + 4)
    )
    for team in ["2", "3", "4", "5", "6"]:
        assert coprs["endGameTowerPoints"][team] == pytest.approx(  # pyre-ignore[16]
            (0 + 4 * 5) / (4 + 4)
        )


def test_compute_coprs_per_robot_skips_partial_alliances() -> None:
    partial = (["frc1", "frc2"], ["frc3", "frc4", "frc5"])

    coprs = MatchstatsHelper.calculate_coprs(_tower_matches(SCHEDULE + [partial]), 2026)

    mean = 120 / 27
    assert coprs["endGameTowerPoints"]["1"] == pytest.approx(  # pyre-ignore[16]
        (120 + 4 * mean) / (4 + 4)
    )
    assert coprs["endGameTowerPoints"]["2"] == pytest.approx(  # pyre-ignore[16]
        (0 + 4 * mean) / (4 + 4)
    )


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

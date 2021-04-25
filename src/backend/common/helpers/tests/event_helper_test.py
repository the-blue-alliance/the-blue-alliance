import datetime
import json
from random import shuffle

import pytest
from freezegun import freeze_time
from google.cloud import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.event_helper import EventHelper, TeamAvgScore
from backend.common.models.alliance import MatchAlliance
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_calculate_avg_score_no_matches() -> None:
    avg_score = EventHelper.calculate_team_avg_score("frc254", [])
    assert avg_score == TeamAvgScore(
        qual_avg=None,
        elim_avg=None,
        all_qual_scores=[],
        all_elim_scores=[],
    )


def test_calculate_avg_score_no_team_matches() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(comp_level=CompLevel.QM, alliances_json=json.dumps(alliance_dict))

    avg_score = EventHelper.calculate_team_avg_score("frc254", [m])
    assert avg_score == TeamAvgScore(
        qual_avg=None,
        elim_avg=None,
        all_qual_scores=[],
        all_elim_scores=[],
    )


def test_calculate_avg_score_all_unplayed() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(comp_level=CompLevel.QM, alliances_json=json.dumps(alliance_dict))

    avg_score = EventHelper.calculate_team_avg_score("frc1", [m])
    assert avg_score == TeamAvgScore(
        qual_avg=None,
        elim_avg=None,
        all_qual_scores=[],
        all_elim_scores=[],
    )


def test_calculate_avg_score_qual_only() -> None:
    m1 = Match(
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=5
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=10
                ),
            }
        ),
    )
    m2 = Match(
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc10", "frc11", "frc12"], score=7
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc13", "frc1", "frc14"], score=3
                ),
            }
        ),
    )

    avg_score = EventHelper.calculate_team_avg_score("frc1", [m1, m2])
    assert avg_score == TeamAvgScore(
        qual_avg=4.0,
        elim_avg=None,
        all_qual_scores=[5, 3],
        all_elim_scores=[],
    )


def test_calculate_avg_score_elim_only() -> None:
    m1 = Match(
        comp_level=CompLevel.QF,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=5
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=10
                ),
            }
        ),
    )
    m2 = Match(
        comp_level=CompLevel.QF,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc10", "frc11", "frc12"], score=7
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc13", "frc1", "frc14"], score=3
                ),
            }
        ),
    )

    avg_score = EventHelper.calculate_team_avg_score("frc1", [m1, m2])
    assert avg_score == TeamAvgScore(
        qual_avg=None,
        elim_avg=4.0,
        all_qual_scores=[],
        all_elim_scores=[5, 3],
    )


def test_calculate_wlt_no_matches() -> None:
    wlt = EventHelper.calculate_wlt("frc254", [])
    assert wlt == WLTRecord(
        wins=0,
        losses=0,
        ties=0,
    )


def test_calculate_wlt_no_team_matches(ndb_context) -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(
        id="2019ct_qm1",
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(alliance_dict),
    )

    wlt = EventHelper.calculate_wlt("frc254", [m])
    assert wlt == WLTRecord(
        wins=0,
        losses=0,
        ties=0,
    )


def test_calculate_wlt_all_unplayed(ndb_context) -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(
        id="2019ct_qm1",
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(alliance_dict),
    )

    wlt = EventHelper.calculate_wlt("frc254", [m])
    assert wlt == WLTRecord(
        wins=0,
        losses=0,
        ties=0,
    )


def test_calculate_wlt(ndb_context) -> None:
    m1 = Match(
        id="2019ct_qm1",
        event=ndb.Key(Event, "2019ct"),
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=10
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=5
                ),
            }
        ),
    )
    m2 = Match(
        id="2019ct_qm2",
        event=ndb.Key(Event, "2019ct"),
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=5
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=5
                ),
            }
        ),
    )
    m3 = Match(
        id="2019ct_qm3",
        event=ndb.Key(Event, "2019ct"),
        comp_level=CompLevel.QM,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=1
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=3
                ),
            }
        ),
    )

    wlt = EventHelper.calculate_wlt("frc1", [m1, m2, m3])
    assert wlt == WLTRecord(wins=1, losses=1, ties=1)


def test_sorted_events_start_date(ndb_context) -> None:
    e1 = Event(
        start_date=datetime.datetime(2010, 2, 21),
        end_date=datetime.datetime(2010, 3, 2),
    )
    e2 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 2),
    )

    events = [e1, e2]
    shuffle(events)

    events = EventHelper.sorted_events(events)
    assert events == [e1, e2]


def test_sorted_events_end_date(ndb_context) -> None:
    e1 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 2),
    )
    e2 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 3),
    )

    events = [e1, e2]
    shuffle(events)

    events = EventHelper.sorted_events(events)
    assert events == [e1, e2]


def test_sorted_events_start_date_end_date(ndb_context) -> None:
    e1 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 3),
    )
    e2 = Event(
        start_date=datetime.datetime(2010, 3, 2),
        end_date=datetime.datetime(2010, 3, 4),
    )
    e3 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 4),
    )
    e4 = Event(
        start_date=datetime.datetime(2002, 3, 1),
        end_date=datetime.datetime(2002, 3, 2),
    )

    expected_order = [e4, e1, e3, e2]

    events = [e1, e2, e3, e4]
    shuffle(events)

    # Ensure compatability with the previous sorting
    events.sort(key=EventHelper.start_date_or_distant_future)
    events.sort(key=EventHelper.end_date_or_distant_future)
    assert events == expected_order

    shuffle(events)

    events = EventHelper.sorted_events(events)
    assert events == expected_order


def test_sorted_events_distant_future_event(ndb_context) -> None:
    e1 = Event()
    e2 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 2),
    )

    events = [e1, e2]
    shuffle(events)

    events = EventHelper.sorted_events(events)
    assert events == [e2, e1]


def test_group_by_week_old_champs(ndb_context) -> None:
    e = Event(event_type_enum=EventType.CMP_DIVISION, year=2010, official=True)
    events = EventHelper.group_by_week([e])
    assert events == {
        "FIRST Championship": [e],
    }


def test_group_by_week_2021_champs(ndb_context) -> None:
    e1 = Event(event_type_enum=EventType.CMP_FINALS, year=2021, official=True)
    e2 = Event(event_type_enum=EventType.CMP_FINALS, year=2021, official=True)
    events = EventHelper.group_by_week([e1, e2])
    assert events == {
        "FIRST Championship": [e1, e2],
    }


def test_group_by_week_two_champs(ndb_context) -> None:
    e1 = Event(
        event_type_enum=EventType.CMP_DIVISION, year=2018, official=True, city="Detriot"
    )
    e2 = Event(
        event_type_enum=EventType.CMP_DIVISION, year=2018, official=True, city="Detriot"
    )
    events = EventHelper.group_by_week([e1, e2])
    assert events == {
        "FIRST Championship - Detriot": [e1, e2],
    }


def test_group_by_week_in_season(ndb_context) -> None:
    e1 = Event(
        event_type_enum=EventType.DISTRICT,
        year=2018,
        start_date=datetime.datetime(2018, 3, 1),
        official=True,
    )
    e2 = Event(
        event_type_enum=EventType.DISTRICT,
        year=2018,
        start_date=datetime.datetime(2018, 3, 1),
        official=True,
    )
    e1._week = 1  # Remmeber, these are 0-indexed
    e2._week = 1
    events = EventHelper.group_by_week([e1, e2])
    assert events == {
        "Week 2": [e1, e2],
    }


def test_group_by_week_in_season_weekless(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.DISTRICT,
        year=2018,
        official=True,
    )
    events = EventHelper.group_by_week([e])
    assert events == {
        "Other Official Events": [e],
    }


def test_group_by_week_offseason(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.OFFSEASON,
        year=2018,
        official=True,
    )
    events = EventHelper.group_by_week([e])
    assert events == {
        "Offseason": [e],
    }


def test_group_by_week_preseason(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.PRESEASON,
        year=2018,
        official=True,
    )
    events = EventHelper.group_by_week([e])
    assert events == {
        "Preseason": [e],
    }


def test_group_by_week_foc(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.FOC,
        year=2018,
        official=True,
    )
    events = EventHelper.group_by_week([e])
    assert events == {
        "FIRST Festival of Champions": [e],
    }


def test_group_by_week_foc_multiple(ndb_context) -> None:
    e1 = Event(
        event_type_enum=EventType.FOC,
        year=2018,
        official=True,
    )
    e2 = Event(
        event_type_enum=EventType.FOC,
        year=2018,
        official=True,
    )
    events = EventHelper.group_by_week([e1, e2])
    assert events == {
        "FIRST Festival of Champions": [e1, e2],
    }


@pytest.mark.parametrize(
    "current_date,expected_event_keys",
    [
        (datetime.datetime(2019, 3, 1), [f"event_{i}" for i in range(1, 4)]),
        (datetime.datetime(2019, 3, 4), [f"event_{i}" for i in range(3, 11)]),
        (datetime.datetime(2019, 3, 6), [f"event_{i}" for i in range(4, 11)]),
    ],
)
def test_get_week_events(ndb_context, current_date, expected_event_keys) -> None:
    # Seed a month of events
    [
        Event(
            id=f"2019event_{day}",
            event_short=f"event_{day}",
            year=2019,
            event_type_enum=EventType.OFFSEASON,
            start_date=datetime.datetime(2019, 3, day),
            end_date=datetime.datetime(2019, 3, day),
        ).put()
        for day in range(1, 30)
    ]

    with freeze_time(current_date):
        events = EventHelper.week_events()
        event_keys = [e.event_short for e in events]
        assert event_keys == expected_event_keys


@pytest.mark.parametrize(
    "start_date, expected_date",
    [
        (None, datetime.datetime(2177, 1, 1, 1, 1, 1)),
        (datetime.datetime(2019, 3, 4), datetime.datetime(2019, 3, 4)),
    ],
)
def test_start_date_or_distant_future(
    start_date: datetime.datetime, expected_date: datetime.datetime
) -> None:
    e = Event(start_date=start_date)
    assert EventHelper.start_date_or_distant_future(e) == expected_date


@pytest.mark.parametrize(
    "end_date, expected_date",
    [
        (None, datetime.datetime(2177, 1, 1, 1, 1, 1)),
        (datetime.datetime(2019, 3, 4), datetime.datetime(2019, 3, 4)),
    ],
)
def test_end_date_or_distant_future(
    end_date: datetime.datetime, expected_date: datetime.datetime
) -> None:
    e = Event(end_date=end_date)
    assert EventHelper.end_date_or_distant_future(e) == expected_date


def test_remapteams_awards(ndb_context) -> None:
    # Ensure we cast str `team_number` to int, when possible
    a1 = Award(
        team_list=[ndb.Key(Team, "frc1")],
        recipient_json_list=[json.dumps({"team_number": "1", "awardee": None})],
    )
    # Ensure remap int `team_number` -> str `team_number`
    a2 = Award(
        team_list=[ndb.Key(Team, "frc200")],
        recipient_json_list=[json.dumps({"team_number": 200, "awardee": None})],
    )
    # Ensure remap str `team_number` -> int `team_number`
    a3 = Award(
        team_list=[ndb.Key(Team, "frc3B")],
        recipient_json_list=[json.dumps({"team_number": "3B", "awardee": None})],
    )
    # Ensure remap of `str` -> `int`
    a4 = Award(
        team_list=[ndb.Key(Team, "frc4")],
        recipient_json_list=[json.dumps({"team_number": 4, "awardee": None})],
    )
    # Ensure int `team_number` as-is if no reampping or casting
    a5 = Award(
        team_list=[ndb.Key(Team, "frc5")],
        recipient_json_list=[json.dumps({"team_number": 5, "awardee": None})],
    )
    # Ensure str `team_number` as-is if no remapping or casting
    a6 = Award(
        team_list=[ndb.Key(Team, "frc6B")],
        recipient_json_list=[json.dumps({"team_number": "6B", "awardee": None})],
    )

    awards = [a1, a2, a3, a4, a5, a6]
    remap_teams = {
        "frc200": "frc2B",
        "frc3B": "frc3",
        "frc4": "frc400",
    }
    EventHelper.remapteams_awards(awards, remap_teams)

    assert a1.recipient_json_list == [json.dumps({"team_number": 1, "awardee": None})]
    assert a1.team_list == [ndb.Key(Team, "frc1")]
    assert a1._dirty

    assert a2.recipient_json_list == [
        json.dumps({"team_number": "2B", "awardee": None})
    ]
    assert a2.team_list == [ndb.Key(Team, "frc2B")]
    assert a2._dirty

    assert a3.recipient_json_list == [json.dumps({"team_number": 3, "awardee": None})]
    assert a3.team_list == [ndb.Key(Team, "frc3")]
    assert a3._dirty

    assert a4.recipient_json_list == [json.dumps({"team_number": 400, "awardee": None})]
    assert a4.team_list == [ndb.Key(Team, "frc400")]
    assert a4._dirty

    assert a5.recipient_json_list == [json.dumps({"team_number": 5, "awardee": None})]
    assert a5.team_list == [ndb.Key(Team, "frc5")]
    assert a5._dirty is False

    assert a6.recipient_json_list == [
        json.dumps({"team_number": "6B", "awardee": None})
    ]
    assert a6.team_list == [ndb.Key(Team, "frc6B")]
    assert a6._dirty is False

import datetime
import json

from google.cloud import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.event_helper import EventHelper, TeamAvgScore
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.match import Match


def test_calculate_avg_score_no_matches() -> None:
    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc254", [])
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

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc254", [m])
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

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc1", [m])
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

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc1", [m1, m2])
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

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc1", [m1, m2])
    assert avg_score == TeamAvgScore(
        qual_avg=None,
        elim_avg=4.0,
        all_qual_scores=[],
        all_elim_scores=[5, 3],
    )


def test_calculate_wlt_no_matches() -> None:
    wlt = EventHelper.calculateTeamWLTFromMatches("frc254", [])
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

    wlt = EventHelper.calculateTeamWLTFromMatches("frc254", [m])
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

    wlt = EventHelper.calculateTeamWLTFromMatches("frc254", [m])
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

    wlt = EventHelper.calculateTeamWLTFromMatches("frc1", [m1, m2, m3])
    assert wlt == WLTRecord(wins=1, losses=1, ties=1)


def test_sort_events(ndb_context) -> None:
    e1 = Event()
    e2 = Event(
        start_date=datetime.datetime(2010, 3, 1),
        end_date=datetime.datetime(2010, 3, 2),
    )

    events = [e1, e2]
    EventHelper.sort_events(events)
    assert events == [e2, e1]


def test_group_by_week_old_champs(ndb_context) -> None:
    e = Event(event_type_enum=EventType.CMP_DIVISION, year=2010, official=True)
    events = EventHelper.groupByWeek([e])
    assert events == {
        "FIRST Championship": [e],
    }


def test_group_by_week_two_champs(ndb_context) -> None:
    e1 = Event(
        event_type_enum=EventType.CMP_DIVISION, year=2018, official=True, city="Detriot"
    )
    e2 = Event(
        event_type_enum=EventType.CMP_DIVISION, year=2018, official=True, city="Detriot"
    )
    events = EventHelper.groupByWeek([e1, e2])
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
    events = EventHelper.groupByWeek([e1, e2])
    assert events == {
        "Week 2": [e1, e2],
    }


def test_group_by_week_in_season_weekless(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.DISTRICT,
        year=2018,
        official=True,
    )
    events = EventHelper.groupByWeek([e])
    assert events == {
        "Other Official Events": [e],
    }


def test_group_by_week_offseason(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.OFFSEASON,
        year=2018,
        official=True,
    )
    events = EventHelper.groupByWeek([e])
    assert events == {
        "Offseason": [e],
    }


def test_group_by_week_preseason(ndb_context) -> None:
    e = Event(
        event_type_enum=EventType.PRESEASON,
        year=2018,
        official=True,
    )
    events = EventHelper.groupByWeek([e])
    assert events == {
        "Preseason": [e],
    }

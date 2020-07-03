import json

from google.cloud import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.event_helper import EventHelper, TeamAvgScore
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.match import Match


def test_calculate_avg_score_no_matches() -> None:
    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc254", [])
    assert avg_score == TeamAvgScore(
        qual_avg=None, elim_avg=None, all_qual_scores=[], all_elim_scores=[],
    )


def test_calculate_avg_score_no_team_matches() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(comp_level=CompLevel.QM, alliances_json=json.dumps(alliance_dict))

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc254", [m])
    assert avg_score == TeamAvgScore(
        qual_avg=None, elim_avg=None, all_qual_scores=[], all_elim_scores=[],
    )


def test_calculate_avg_score_all_unplayed() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    m = Match(comp_level=CompLevel.QM, alliances_json=json.dumps(alliance_dict))

    avg_score = EventHelper.calculateTeamAvgScoreFromMatches("frc1", [m])
    assert avg_score == TeamAvgScore(
        qual_avg=None, elim_avg=None, all_qual_scores=[], all_elim_scores=[],
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
        qual_avg=4.0, elim_avg=None, all_qual_scores=[5, 3], all_elim_scores=[],
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
        qual_avg=None, elim_avg=4.0, all_qual_scores=[], all_elim_scores=[5, 3],
    )


def test_calculate_wlt_no_matches() -> None:
    wlt = EventHelper.calculateTeamWLTFromMatches("frc254", [])
    assert wlt == WLTRecord(wins=0, losses=0, ties=0,)


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
    assert wlt == WLTRecord(wins=0, losses=0, ties=0,)


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
    assert wlt == WLTRecord(wins=0, losses=0, ties=0,)


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

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_streak_helper import (
    ConsecutiveEventWinsCalculator,
    ConsecutiveImpactWinsCalculator,
    ConsecutiveMatchWinsCalculator,
    InsightsStreakCalculator,
)
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team


def _make_team(number: int) -> None:
    Team(id=f"frc{number}", team_number=number).put()


def _make_regional(event_id: str, year: int) -> None:
    Event(
        id=event_id,
        year=year,
        event_short=event_id[4:],
        event_type_enum=EventType.REGIONAL,
    ).put()


def _make_winner_award(event_id: str, year: int, team_ids: list) -> None:
    Award(
        id=f"{event_id}_winner",
        year=year,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, event_id),
        name_str="Winner",
        team_list=[ndb.Key(Team, tid) for tid in team_ids],
    ).put()


def _make_match(
    match_id: str,
    event_id: str,
    year: int,
    red_teams: list,
    blue_teams: list,
    red_score: int,
    blue_score: int,
) -> None:
    import json

    alliances = {
        "red": {"teams": red_teams, "score": red_score},
        "blue": {"teams": blue_teams, "score": blue_score},
    }
    Match(
        id=match_id,
        year=year,
        event=ndb.Key(Event, event_id),
        comp_level="qm",
        set_number=1,
        match_number=int(match_id.split("m")[-1]),
        alliances_json=json.dumps(alliances),
        team_key_names=red_teams + blue_teams,
    ).put()


def _make_event_team(event_id: str, team_id: str, year: int) -> None:
    EventTeam(
        id=f"{event_id}_{team_id}",
        event=ndb.Key(Event, event_id),
        team=ndb.Key(Team, team_id),
        year=year,
    ).put()


def _make_impact_award(event_id: str, year: int, team_ids: list) -> None:
    Award(
        id=f"{event_id}_chairmans",
        year=year,
        award_type_enum=AwardType.CHAIRMANS,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, event_id),
        name_str="Chairman's Award",
        team_list=[ndb.Key(Team, tid) for tid in team_ids],
    ).put()


def test_consecutive_event_wins(ndb_stub) -> None:
    """Team wins 3 events in a row, verify streak of 3 marked active."""
    _make_team(1323)
    _make_team(100)

    for i, eid in enumerate(["2024ev1", "2024ev2", "2024ev3"]):
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc1323"])
        # Add a match so event isn't skipped
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc1323", "frc100", "frc100"],
            ["frc100", "frc100", "frc100"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    insight = insights[0]
    entries = insight.data["entries"]
    assert len(entries) == 1
    assert entries[0]["team_key"] == "frc1323"
    assert entries[0]["streak_length"] == 3
    assert entries[0]["is_active"] is True
    assert entries[0]["first"] == "2024ev1"
    assert entries[0]["last"] == "2024ev3"


def test_consecutive_event_wins_streak_broken(ndb_stub) -> None:
    """Team wins 2, loses 1, wins 1. Two streaks: inactive(2) and active(1)."""
    _make_team(1323)
    _make_team(100)
    _make_team(200)

    # Win ev1 and ev2
    for eid in ["2024ev1", "2024ev2"]:
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc1323"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc1323", "frc100", "frc100"],
            ["frc100", "frc100", "frc100"],
            10,
            5,
        )

    # Attend ev3 but don't win (frc200 wins)
    _make_regional("2024ev3", 2024)
    _make_winner_award("2024ev3", 2024, ["frc200"])
    _make_event_team("2024ev3", "frc1323", 2024)
    _make_match(
        "2024ev3_qm1",
        "2024ev3",
        2024,
        ["frc1323", "frc100", "frc100"],
        ["frc200", "frc100", "frc100"],
        5,
        10,
    )

    # Win ev4
    _make_regional("2024ev4", 2024)
    _make_winner_award("2024ev4", 2024, ["frc1323"])
    _make_match(
        "2024ev4_qm1",
        "2024ev4",
        2024,
        ["frc1323", "frc100", "frc100"],
        ["frc100", "frc100", "frc100"],
        10,
        5,
    )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    # Should have two entries for frc1323: inactive(2), active(1)
    team_entries = [e for e in entries if e["team_key"] == "frc1323"]
    assert len(team_entries) == 2

    inactive = [e for e in team_entries if not e["is_active"]]
    active = [e for e in team_entries if e["is_active"]]

    assert len(inactive) == 1
    assert inactive[0]["streak_length"] == 2
    assert inactive[0]["first"] == "2024ev1"
    assert inactive[0]["last"] == "2024ev2"
    assert len(active) == 1
    assert active[0]["streak_length"] == 1
    assert active[0]["first"] == "2024ev4"
    assert active[0]["last"] == "2024ev4"


def test_multiple_streaks_per_team(ndb_stub) -> None:
    """Team has an inactive streak and an active streak. Both appear."""
    _make_team(1323)
    _make_team(100)
    _make_team(200)

    events = [
        ("2024ev1", True),
        ("2024ev2", True),
        ("2024ev3", True),
        ("2024ev4", False),  # break
        ("2024ev5", True),
        ("2024ev6", True),
    ]

    for eid, wins in events:
        _make_regional(eid, 2024)
        if wins:
            _make_winner_award(eid, 2024, ["frc1323"])
        else:
            _make_winner_award(eid, 2024, ["frc200"])
        _make_event_team(eid, "frc1323", 2024)
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc1323", "frc100", "frc100"],
            ["frc200", "frc100", "frc100"],
            10 if wins else 5,
            5 if wins else 10,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    team_entries = [e for e in entries if e["team_key"] == "frc1323"]
    assert len(team_entries) == 2

    # Sorted by streak_length desc
    assert team_entries[0]["streak_length"] == 3
    assert team_entries[0]["is_active"] is False
    assert team_entries[0]["first"] == "2024ev1"
    assert team_entries[0]["last"] == "2024ev3"
    assert team_entries[1]["streak_length"] == 2
    assert team_entries[1]["is_active"] is True
    assert team_entries[1]["first"] == "2024ev5"
    assert team_entries[1]["last"] == "2024ev6"


def test_active_vs_inactive(ndb_stub) -> None:
    """Active streaks have is_active=True, broken ones have is_active=False."""
    _make_team(1)
    _make_team(2)
    _make_team(100)
    _make_team(200)

    # frc1: wins 2 events then breaks
    for eid in ["2024a1", "2024a2"]:
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc1"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc1", "frc100", "frc100"],
            ["frc200", "frc100", "frc100"],
            10,
            5,
        )

    _make_regional("2024a3", 2024)
    _make_winner_award("2024a3", 2024, ["frc200"])
    _make_event_team("2024a3", "frc1", 2024)
    _make_match(
        "2024a3_qm1",
        "2024a3",
        2024,
        ["frc1", "frc100", "frc100"],
        ["frc200", "frc100", "frc100"],
        5,
        10,
    )

    # frc2: wins 2 events, still active (doesn't attend a3)
    for eid in ["2024b1", "2024b2"]:
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc2"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc2", "frc100", "frc100"],
            ["frc200", "frc100", "frc100"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    frc2_entries = [e for e in entries if e["team_key"] == "frc2"]

    assert len(frc1_entries) == 1
    assert frc1_entries[0]["is_active"] is False
    assert frc1_entries[0]["streak_length"] == 2

    assert len(frc2_entries) == 1
    assert frc2_entries[0]["is_active"] is True
    assert frc2_entries[0]["streak_length"] == 2


def test_consecutive_match_wins_real_event(ndb_stub, test_data_importer) -> None:
    """Use real 2025mabos match data to verify consecutive match win streak calculation.

    frc125 went 14-0 from qm6 through sf7m1, then lost sf11m1, then won
    sf13m1/f1m1/f1m2 to finish the event. Verify both streaks are detected.
    """
    Event(
        id="2025mabos",
        year=2025,
        event_short="mabos",
        event_type_enum=EventType.REGIONAL,
    ).put()

    test_data_importer.import_match_list(__file__, "data/2025mabos_matches.json")

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveMatchWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc125_entries = [e for e in entries if e["team_key"] == "frc125"]
    assert len(frc125_entries) == 2

    inactive = [e for e in frc125_entries if not e["is_active"]]
    active = [e for e in frc125_entries if e["is_active"]]

    assert len(inactive) == 1
    assert inactive[0]["streak_length"] == 14
    assert inactive[0]["first"] == "2025mabos_qm6"
    assert inactive[0]["last"] == "2025mabos_sf7m1"

    assert len(active) == 1
    assert active[0]["streak_length"] == 3
    assert active[0]["first"] == "2025mabos_sf13m1"
    assert active[0]["last"] == "2025mabos_f1m2"

    assert entries[0]["team_key"] == "frc125"
    assert entries[0]["streak_length"] == 14

    frc6201_entries = [e for e in entries if e["team_key"] == "frc6201"]
    assert len(frc6201_entries) == 2

    frc6201_inactive = sorted(
        [e for e in frc6201_entries if not e["is_active"]],
        key=lambda e: -e["streak_length"],
    )
    assert frc6201_inactive[0]["streak_length"] == 10
    assert frc6201_inactive[0]["first"] == "2025mabos_qm2"
    assert frc6201_inactive[0]["last"] == "2025mabos_qm59"

    assert frc6201_inactive[1]["streak_length"] == 4
    assert frc6201_inactive[1]["first"] == "2025mabos_qm75"
    assert frc6201_inactive[1]["last"] == "2025mabos_sf11m1"

    assert all(not e["is_active"] for e in frc6201_entries)


def test_consecutive_match_wins(ndb_stub) -> None:
    """Verify correct match win streak length."""
    _make_team(1)
    _make_team(2)
    _make_team(3)
    _make_team(4)
    _make_team(5)
    _make_team(6)

    _make_regional("2024ev1", 2024)

    # frc1 wins 3 matches in a row
    for i in range(1, 4):
        _make_match(
            f"2024ev1_qm{i}",
            "2024ev1",
            2024,
            ["frc1", "frc2", "frc3"],
            ["frc4", "frc5", "frc6"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveMatchWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    assert len(frc1_entries) == 1
    assert frc1_entries[0]["streak_length"] == 3
    assert frc1_entries[0]["is_active"] is True
    assert frc1_entries[0]["first"] == "2024ev1_qm1"
    assert frc1_entries[0]["last"] == "2024ev1_qm3"


def test_match_streak_resets_on_loss(ndb_stub) -> None:
    """Loss resets streak, creates completed entry."""
    _make_team(1)
    _make_team(2)
    _make_team(3)
    _make_team(4)
    _make_team(5)
    _make_team(6)

    _make_regional("2024ev1", 2024)

    # frc1 wins 2 matches
    for i in range(1, 3):
        _make_match(
            f"2024ev1_qm{i}",
            "2024ev1",
            2024,
            ["frc1", "frc2", "frc3"],
            ["frc4", "frc5", "frc6"],
            10,
            5,
        )

    # frc1 loses match 3
    _make_match(
        "2024ev1_qm3",
        "2024ev1",
        2024,
        ["frc1", "frc2", "frc3"],
        ["frc4", "frc5", "frc6"],
        5,
        10,
    )

    # frc1 wins match 4
    _make_match(
        "2024ev1_qm4",
        "2024ev1",
        2024,
        ["frc1", "frc2", "frc3"],
        ["frc4", "frc5", "frc6"],
        10,
        5,
    )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveMatchWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    assert len(frc1_entries) == 2

    inactive = [e for e in frc1_entries if not e["is_active"]]
    active = [e for e in frc1_entries if e["is_active"]]

    assert len(inactive) == 1
    assert inactive[0]["streak_length"] == 2
    assert inactive[0]["first"] == "2024ev1_qm1"
    assert inactive[0]["last"] == "2024ev1_qm2"
    assert len(active) == 1
    assert active[0]["streak_length"] == 1
    assert active[0]["first"] == "2024ev1_qm4"
    assert active[0]["last"] == "2024ev1_qm4"


def test_match_streak_tie_resets(ndb_stub) -> None:
    """Tie resets match win streak."""
    _make_team(1)
    _make_team(2)
    _make_team(3)
    _make_team(4)
    _make_team(5)
    _make_team(6)

    _make_regional("2024ev1", 2024)

    # frc1 wins 2 matches
    for i in range(1, 3):
        _make_match(
            f"2024ev1_qm{i}",
            "2024ev1",
            2024,
            ["frc1", "frc2", "frc3"],
            ["frc4", "frc5", "frc6"],
            10,
            5,
        )

    # Tie in match 3
    _make_match(
        "2024ev1_qm3",
        "2024ev1",
        2024,
        ["frc1", "frc2", "frc3"],
        ["frc4", "frc5", "frc6"],
        10,
        10,
    )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveMatchWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    assert len(frc1_entries) == 1
    assert frc1_entries[0]["streak_length"] == 2
    assert frc1_entries[0]["is_active"] is False
    assert frc1_entries[0]["first"] == "2024ev1_qm1"
    assert frc1_entries[0]["last"] == "2024ev1_qm2"


def test_consecutive_impact_wins(ndb_stub) -> None:
    """Team wins Impact 3 years running, verify year-type streak of 3."""
    _make_team(1)
    _make_team(100)

    for year in [2022, 2023, 2024]:
        eid = f"{year}ev1"
        _make_regional(eid, year)
        _make_impact_award(eid, year, ["frc1"])
        _make_match(
            f"{eid}_qm1",
            eid,
            year,
            ["frc1", "frc100", "frc100"],
            ["frc100", "frc100", "frc100"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveImpactWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    assert len(frc1_entries) == 1
    assert frc1_entries[0]["streak_length"] == 3
    assert frc1_entries[0]["is_active"] is True
    assert frc1_entries[0]["first"] == "2022"
    assert frc1_entries[0]["last"] == "2024"
    assert insights[0].data["streak_type"] == "year"


def test_consecutive_impact_wins_across_covid(ndb_stub) -> None:
    """Streak bridges 2019->2022 gap (COVID years treated as consecutive)."""
    _make_team(1)
    _make_team(100)

    for year in [2018, 2019, 2022, 2023]:
        eid = f"{year}ev1"
        _make_regional(eid, year)
        _make_impact_award(eid, year, ["frc1"])
        _make_match(
            f"{eid}_qm1",
            eid,
            year,
            ["frc1", "frc100", "frc100"],
            ["frc100", "frc100", "frc100"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveImpactWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    frc1_entries = [e for e in entries if e["team_key"] == "frc1"]
    assert len(frc1_entries) == 1
    assert frc1_entries[0]["streak_length"] == 4
    assert frc1_entries[0]["is_active"] is True
    assert frc1_entries[0]["first"] == "2018"
    assert frc1_entries[0]["last"] == "2023"


def test_top_25_limit(ndb_stub) -> None:
    """Only top ~25 streak entries appear in output."""
    _make_team(999)

    # Create 30 teams, each with a streak of 1 (active)
    for i in range(1, 31):
        _make_team(i)
        eid = f"2024e{i}"
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, [f"frc{i}"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            [f"frc{i}", "frc999", "frc999"],
            ["frc999", "frc999", "frc999"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]
    assert len(entries) == 25


def test_streaks_sorted_by_length(ndb_stub) -> None:
    """Output is sorted by streak_length descending."""
    _make_team(1)
    _make_team(2)
    _make_team(3)
    _make_team(100)
    _make_team(200)

    # frc1: 1 win streak
    _make_regional("2024a1", 2024)
    _make_winner_award("2024a1", 2024, ["frc1"])
    _make_match(
        "2024a1_qm1",
        "2024a1",
        2024,
        ["frc1", "frc100", "frc100"],
        ["frc200", "frc100", "frc100"],
        10,
        5,
    )

    # frc2: 3 win streak
    for i, eid in enumerate(["2024b1", "2024b2", "2024b3"]):
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc2"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc2", "frc100", "frc100"],
            ["frc200", "frc100", "frc100"],
            10,
            5,
        )

    # frc3: 2 win streak
    for eid in ["2024c1", "2024c2"]:
        _make_regional(eid, 2024)
        _make_winner_award(eid, 2024, ["frc3"])
        _make_match(
            f"{eid}_qm1",
            eid,
            2024,
            ["frc3", "frc100", "frc100"],
            ["frc200", "frc100", "frc100"],
            10,
            5,
        )

    insights = InsightsStreakCalculator.make_insights(
        year=0,
        calculators=[ConsecutiveEventWinsCalculator()],
    )

    assert len(insights) == 1
    entries = insights[0].data["entries"]

    assert entries[0]["team_key"] == "frc2"
    assert entries[0]["streak_length"] == 3
    assert entries[1]["team_key"] == "frc3"
    assert entries[1]["streak_length"] == 2
    assert entries[2]["team_key"] == "frc1"
    assert entries[2]["streak_length"] == 1

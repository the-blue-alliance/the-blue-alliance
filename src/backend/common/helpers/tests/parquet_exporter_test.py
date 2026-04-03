import json

from google.appengine.ext import ndb

from backend.common.helpers.parquet_exporter import (
    flatten_match,
    flatten_team,
    MATCH_SCHEMA,
    matches_to_table,
    TEAM_SCHEMA,
    teams_to_table,
)
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_flatten_match(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        event_short="test",
        event_type_enum=0,
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=ndb.Key(Event, "2024test"),
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {
                    "teams": ["frc27", "frc254", "frc1678"],
                    "surrogates": [],
                    "dqs": [],
                    "score": 150,
                },
                "blue": {
                    "teams": ["frc971", "frc118", "frc2056"],
                    "surrogates": ["frc118"],
                    "dqs": [],
                    "score": 130,
                },
            }
        ),
        team_key_names=["frc27", "frc254", "frc1678", "frc971", "frc118", "frc2056"],
    )
    match.put()

    row = flatten_match(match)

    assert row["key"] == "2024test_qm1"
    assert row["event_key"] == "2024test"
    assert row["year"] == 2024
    assert row["comp_level"] == "qm"
    assert row["red_score"] == 150
    assert row["blue_score"] == 130
    assert row["red_teams"] == ["frc27", "frc254", "frc1678"]
    assert row["blue_teams"] == ["frc971", "frc118", "frc2056"]
    assert row["blue_surrogate_teams"] == ["frc118"]
    assert row["winning_alliance"] == "red"


def test_flatten_match_unplayed(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        event_short="test",
        event_type_enum=0,
    )
    event.put()

    match = Match(
        id="2024test_qm2",
        event=ndb.Key(Event, "2024test"),
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=2,
        alliances_json=json.dumps(
            {
                "red": {
                    "teams": ["frc27"],
                    "score": -1,
                },
                "blue": {
                    "teams": ["frc254"],
                    "score": -1,
                },
            }
        ),
        team_key_names=["frc27", "frc254"],
    )
    match.put()

    row = flatten_match(match)
    assert row["red_score"] is None
    assert row["blue_score"] is None


def test_flatten_team(ndb_stub) -> None:
    team = Team(
        id="frc27",
        team_number=27,
        name="  Team 27  ",
        nickname="Rush",
        city="Rochester",
        state_prov="New York",
        country="USA",
        rookie_year=1997,
    )
    team.put()

    row = flatten_team(team)
    assert row["key"] == "frc27"
    assert row["team_number"] == 27
    assert row["name"] == "Team 27"
    assert row["nickname"] == "Rush"
    assert row["city"] == "Rochester"
    assert row["rookie_year"] == 1997


def test_flatten_team_empty_strings(ndb_stub) -> None:
    team = Team(
        id="frc9999",
        team_number=9999,
        name="",
        nickname="  ",
    )
    team.put()

    row = flatten_team(team)
    assert row["name"] is None
    assert row["nickname"] is None


def test_matches_to_table_empty(ndb_stub) -> None:
    table = matches_to_table([])
    assert table.num_rows == 0
    assert table.schema == MATCH_SCHEMA


def test_matches_to_table(ndb_stub) -> None:
    event = Event(
        id="2024test",
        year=2024,
        event_short="test",
        event_type_enum=0,
    )
    event.put()

    match = Match(
        id="2024test_qm1",
        event=ndb.Key(Event, "2024test"),
        year=2024,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {"teams": ["frc27"], "score": 100},
                "blue": {"teams": ["frc254"], "score": 90},
            }
        ),
        team_key_names=["frc27", "frc254"],
    )
    match.put()

    table = matches_to_table([match])
    assert table.num_rows == 1
    assert table.schema == MATCH_SCHEMA

    row = table.to_pydict()
    assert row["red_teams"] == [["frc27"]]
    assert row["blue_teams"] == [["frc254"]]


def test_teams_to_table(ndb_stub) -> None:
    team = Team(
        id="frc27",
        team_number=27,
        nickname="Rush",
        rookie_year=1997,
    )
    team.put()

    table = teams_to_table([team])
    assert table.num_rows == 1
    assert table.schema == TEAM_SCHEMA

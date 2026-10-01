import json
from typing import List
from unittest.mock import patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_ranking import EventRanking
from backend.common.models.match import Match
from backend.common.models.team import Team


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
    EventRemapTeamsHelper.remapteams_awards(awards, remap_teams)

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


def test_remapteams_matches(ndb_context):
    matches = [
        Match(
            id="2019casj_qm1",
            alliances_json="""{"blue": {"score": 100, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 200, "teams": ["frc4", "frc5", "frc9001"]}}""",
        )
    ]
    EventRemapTeamsHelper.remapteams_matches(
        matches,
        {
            "frc9001": "frc1B",
            "frc2": "frc200",
        },
    )
    assert matches[0].alliances["blue"]["teams"] == ["frc1", "frc200", "frc3"]
    assert set(matches[0].team_key_names) == set(
        ["frc4", "frc5", "frc1B", "frc1", "frc200", "frc3"]
    )


def test_remap_alliances(ndb_context):
    alliances = [
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 1",
            "picks": ["frc9001", "frc649", "frc840"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 2",
            "picks": ["frc254", "frc5499", "frc6418"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 3",
            "picks": ["frc1868", "frc8", "frc4990"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 4",
            "picks": ["frc604", "frc2", "frc7308"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 5",
            "picks": ["frc199", "frc5026", "frc192"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 6",
            "picks": ["frc4669", "frc2220", "frc766"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 7",
            "picks": ["frc7419", "frc7667", "frc751"],
        },
        {
            "declines": [],
            "backup": None,
            "name": "Alliance 8",
            "picks": ["frc2367", "frc2473", "frc6241"],
        },
    ]
    EventRemapTeamsHelper.remapteams_alliances(
        alliances,
        {
            "frc9001": "frc1B",
            "frc2": "frc200",
        },
    )
    assert alliances[0]["picks"] == ["frc1B", "frc649", "frc840"]
    assert alliances[3]["picks"] == ["frc604", "frc200", "frc7308"]


def test_remap_rankings2(ndb_context):
    rankings: List[EventRanking] = [
        EventRanking(
            rank=1,
            team_key="frc254",
            record=None,
            qual_average=None,
            matches_played=1,
            dq=0,
            sort_orders=[],
        ),
        EventRanking(
            rank=1,
            team_key="frc9001",
            record=None,
            qual_average=None,
            matches_played=1,
            dq=0,
            sort_orders=[],
        ),
        EventRanking(
            rank=1,
            team_key="frc2",
            record=None,
            qual_average=None,
            matches_played=1,
            dq=0,
            sort_orders=[],
        ),
    ]

    EventRemapTeamsHelper.remapteams_rankings2(
        rankings,
        {
            "frc9001": "frc1B",
            "frc2": "frc200",
        },
    )
    assert rankings[0]["team_key"] == "frc254"
    assert rankings[1]["team_key"] == "frc1B"
    assert rankings[2]["team_key"] == "frc200"


def test_remap_teams_missing_event(ndb_context) -> None:
    assert EventRemapTeamsHelper.remap_teams("2019casj") is None


def test_remap_teams_nothing_to_remap(ndb_context) -> None:
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    with patch.object(EventRemapTeamsHelper, "remapteams_matches") as mock_remap:
        EventRemapTeamsHelper.remap_teams("2019casj")
    mock_remap.assert_not_called()


def test_remap_teams(ndb_context, taskqueue_stub) -> None:
    event = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        remap_teams={"frc9001": "frc1B"},
    )
    event.put()
    Match(
        id="2019casj_qm1",
        event=event.key,
        year=2019,
        comp_level="qm",
        set_number=1,
        match_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc9001"],
        alliances_json=json.dumps(
            {
                "blue": {"score": 100, "teams": ["frc1", "frc2", "frc3"]},
                "red": {"score": 200, "teams": ["frc4", "frc5", "frc9001"]},
            }
        ),
    ).put()
    EventDetails(
        id="2019casj",
        alliance_selections=[
            {"declines": [], "backup": None, "name": "A1", "picks": ["frc9001"]}
        ],
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc9001",
                record=None,
                qual_average=None,
                matches_played=1,
                dq=0,
                sort_orders=[],
            )
        ],
    ).put()
    Award(
        id="2019casj_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=event.key,
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc9001")],
        recipient_json_list=[json.dumps({"team_number": 9001, "awardee": None})],
    ).put()

    EventRemapTeamsHelper.remap_teams("2019casj")

    match = none_throws(Match.get_by_id("2019casj_qm1"))
    assert match.alliances[AllianceColor.RED]["teams"] == ["frc4", "frc5", "frc1B"]
    details = none_throws(EventDetails.get_by_id("2019casj"))
    assert none_throws(details.alliance_selections)[0]["picks"] == ["frc1B"]
    assert none_throws(details.rankings2)[0]["team_key"] == "frc1B"
    award = none_throws(Award.get_by_id("2019casj_1"))
    assert award.team_list == [ndb.Key(Team, "frc1B")]

from google.appengine.ext import ndb

from backend.api.handlers.helpers.add_alliance_status import add_alliance_status
from backend.common.consts.comp_level import CompLevel
from backend.common.models.alliance import EventAlliance
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import (
    EventTeamPlayoffStatus,
    EventTeamStatus,
    EventTeamStatusAlliance,
    EventTeamStatusPlayoff,
)


def update_event_team(
    event_key: str,
    team_number: int,
    alliance_number: int,
    playoff_status: EventTeamStatusPlayoff,
) -> None:
    EventTeam(
        id=f"{event_key}_frc{team_number}",
        event=ndb.Key("Event", event_key),
        team=ndb.Key("Team", team_number),
        status=EventTeamStatus(
            alliance=EventTeamStatusAlliance(number=alliance_number, pick=0),
            playoff=playoff_status,
        ),
    ).put()


def test_unknown_status(ndb_stub):
    event_key = "2021cc"
    alliances = [
        EventAlliance(picks=["frc1", "frc2", "frc3"]),
        EventAlliance(picks=["frc4", "frc5", "frc6"]),
        EventAlliance(picks=["frc7", "frc8", "frc9"]),
        EventAlliance(picks=["frc10", "frc11", "frc12"]),
    ]

    add_alliance_status(event_key, alliances)
    assert len(alliances) == 4
    for alliance in alliances:
        assert alliance["status"] == "unknown"


def test_has_status(ndb_stub):
    event_key = "2021cc"
    alliances = [
        EventAlliance(picks=["frc1", "frc2", "frc3"]),
        EventAlliance(picks=["frc4", "frc5", "frc6"]),
        EventAlliance(picks=["frc7", "frc8", "frc9"]),
        EventAlliance(picks=["frc10", "frc11", "frc12"]),
    ]
    alliance_0_playoff_status = EventTeamStatusPlayoff(
        level=CompLevel.QF, status=EventTeamPlayoffStatus.PLAYING
    )
    alliance_1_playoff_status = EventTeamStatusPlayoff(
        level=CompLevel.SF, status=EventTeamPlayoffStatus.ELIMINATED
    )
    alliance_2_playoff_status = EventTeamStatusPlayoff(
        level=CompLevel.F, status=EventTeamPlayoffStatus.PLAYING
    )
    alliance_3_playoff_status = EventTeamStatusPlayoff(
        level=CompLevel.QF, status=EventTeamPlayoffStatus.WON
    )

    update_event_team(event_key, 1, 0, alliance_0_playoff_status)
    update_event_team(event_key, 4, 1, alliance_1_playoff_status)
    update_event_team(event_key, 7, 2, alliance_2_playoff_status)
    update_event_team(event_key, 10, 3, alliance_3_playoff_status)

    add_alliance_status(event_key, alliances)
    assert len(alliances) == 4
    assert alliances[0]["status"] == alliance_0_playoff_status
    assert alliances[1]["status"] == alliance_1_playoff_status
    assert alliances[2]["status"] == alliance_2_playoff_status
    assert alliances[3]["status"] == alliance_3_playoff_status

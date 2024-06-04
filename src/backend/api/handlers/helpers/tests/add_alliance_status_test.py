from google.appengine.ext import ndb

from backend.api.handlers.helpers.add_alliance_status import add_alliance_status
from backend.common.consts.comp_level import CompLevel
from backend.common.models.alliance import (
    EventAlliance,
    PlayoffAllianceStatus,
    PlayoffOutcome,
)
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import (
    EventTeamStatus,
    EventTeamStatusAlliance,
)


def update_event_team(
    event_key: str,
    team_number: int,
    alliance_number: int,
    playoff_status: PlayoffAllianceStatus,
) -> None:
    EventTeam(
        id=f"{event_key}_frc{team_number}",
        event=ndb.Key("Event", event_key),
        team=ndb.Key("Team", f"frc{team_number}"),
        year=int(event_key[:4]),
        status=EventTeamStatus(
            qual=None,
            playoff=playoff_status,
            alliance=EventTeamStatusAlliance(
                name=None,
                number=alliance_number,
                pick=0,
                backup=None,
            ),
            last_match_key=None,
            next_match_key=None,
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
        assert "status" not in alliance


def test_has_status(ndb_stub):
    event_key = "2021cc"
    alliances = [
        EventAlliance(picks=["frc1", "frc2", "frc3"]),
        EventAlliance(picks=["frc4", "frc5", "frc6"]),
        EventAlliance(picks=["frc7", "frc8", "frc9"]),
        EventAlliance(picks=["frc10", "frc11", "frc12"]),
    ]
    alliance_0_playoff_status = PlayoffAllianceStatus(
        level=CompLevel.QF, status=PlayoffOutcome.PLAYING
    )
    alliance_1_playoff_status = PlayoffAllianceStatus(
        level=CompLevel.SF, status=PlayoffOutcome.ELIMINATED
    )
    alliance_2_playoff_status = PlayoffAllianceStatus(
        level=CompLevel.F, status=PlayoffOutcome.PLAYING
    )
    alliance_3_playoff_status = PlayoffAllianceStatus(
        level=CompLevel.QF, status=PlayoffOutcome.WON
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

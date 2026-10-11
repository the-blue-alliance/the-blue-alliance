import pytest
from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team import Team


@pytest.mark.parametrize("key", ["2010ct_frc177", "2012ct1_frc1"])
def test_valid_key_names(key: str) -> None:
    assert EventTeam.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["frc177_2010ct", "2010ctfrc177", "asdf"])
def test_invalid_key_name(key: str) -> None:
    assert EventTeam.validate_key_name(key) is False


def test_key_name() -> None:
    et = EventTeam(
        id="2010ct_frc177",
        event=ndb.Key(Event, "2010ct"),
        team=ndb.Key(Team, "frc177"),
        year=2010,
    )
    assert et.key_name == "2010ct_frc177"


def test_status_strings_no_status() -> None:
    et = EventTeam(
        id="2010ct_frc177",
        event=ndb.Key(Event, "2010ct"),
        team=ndb.Key(Team, "frc177"),
        year=2010,
    )
    assert et.status_strings == {
        "alliance": "--",
        "playoff": "--",
        "overall": "Team 177 is waiting for the event to begin.",
    }


def test_competing_team_key_defaults_to_team() -> None:
    et = EventTeam(
        id="2026nhmm_frc9997",
        event=ndb.Key(Event, "2026nhmm"),
        team=ndb.Key(Team, "frc9997"),
        year=2026,
    )
    assert et.competing_team_key == "frc9997"


def test_competing_team_key_uses_remapped_to() -> None:
    et = EventTeam(
        id="2026nhmm_frc9997",
        event=ndb.Key(Event, "2026nhmm"),
        team=ndb.Key(Team, "frc9997"),
        year=2026,
        remapped_to="frc3467B",
    )
    assert et.competing_team_key == "frc3467B"


def test_status_strings_use_remapped_to() -> None:
    et = EventTeam(
        id="2026nhmm_frc9997",
        event=ndb.Key(Event, "2026nhmm"),
        team=ndb.Key(Team, "frc9997"),
        year=2026,
        remapped_to="frc3467B",
    )
    assert (
        et.status_strings["overall"] == "Team 3467B is waiting for the event to begin."
    )

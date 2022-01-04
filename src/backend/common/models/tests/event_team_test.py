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
        event=ndb.Key(Event, "2010ct"),
        team=ndb.Key(Team, "frc177"),
    )
    assert et.key_name == "2010ct_frc177"

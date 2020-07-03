import pytest

from google.cloud import ndb

from backend.common.models.robot import Robot
from backend.common.models.team import Team


@pytest.mark.parametrize("key", ["frc177_2010", "frc1_2020"])
def test_valid_key_names(key: str) -> None:
    assert Robot.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["2010_frc177", "frc1772020", "frc177_asdf"])
def test_invalid_key_names(key: str) -> None:
    assert Robot.validate_key_name(key) is False


def test_key_name() -> None:
    robot = Robot(id="frc254_2019", year=2019, team=ndb.Key(Team, "frc254"))
    assert robot.key_name == "frc254_2019"

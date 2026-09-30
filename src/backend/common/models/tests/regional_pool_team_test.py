import pytest
from google.appengine.ext import ndb

from backend.common.models.regional_pool_team import RegionalPoolTeam
from backend.common.models.team import Team


def test_key_name() -> None:
    pool_team = RegionalPoolTeam(
        id="2025_frc254", team=ndb.Key(Team, "frc254"), year=2025
    )
    assert pool_team.key_name == "2025_frc254"
    assert RegionalPoolTeam.render_key_name(2025, "frc254") == "2025_frc254"
    assert pool_team._affected_references == {"year": set()}


@pytest.mark.parametrize(
    "key, valid",
    [
        ("2025_frc254", True),
        # Before the regional pool existed
        ("2024_frc254", False),
        ("2025_254", False),
        ("2025_frc254_extra", False),
        ("frc254", False),
        # Non-numeric year
        ("abcd_frc254", False),
    ],
)
def test_validate_key_name(key: str, valid: bool) -> None:
    # validate_key_name is declared as a @staticmethod but still takes `cls`
    # as its first parameter, so the class has to be passed explicitly.
    assert RegionalPoolTeam.validate_key_name(RegionalPoolTeam, key) is valid


def test_validate_key_name_requires_explicit_cls() -> None:
    # Documents the staticmethod/cls mismatch: calling it like every other
    # model's validate_key_name consumes the key as `cls` and blows up.
    with pytest.raises(TypeError):
        RegionalPoolTeam.validate_key_name("2025_frc254")  # pyre-ignore[20]

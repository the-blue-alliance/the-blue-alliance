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

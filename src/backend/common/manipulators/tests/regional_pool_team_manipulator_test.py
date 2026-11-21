import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.manipulators.regional_pool_team_manipulator import (
    RegionalPoolTeamManipulator,
)
from backend.common.models.regional_pool_team import RegionalPoolTeam
from backend.common.models.team import Team
from backend.common.queries.team_query import RegionalTeamsQuery


@pytest.fixture
def old_regional_pool_team() -> RegionalPoolTeam:
    return RegionalPoolTeam(
        id=RegionalPoolTeam.render_key_name(2025, "frc254"),
        team=ndb.Key(Team, "frc254"),
        year=2025,
    )


@pytest.fixture
def new_regional_pool_team() -> RegionalPoolTeam:
    return RegionalPoolTeam(
        id=RegionalPoolTeam.render_key_name(2025, "frc254"),
        team=ndb.Key(Team, "frc254"),
        year=2025,
    )


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_createOrUpdate(
    old_regional_pool_team: RegionalPoolTeam,
    new_regional_pool_team: RegionalPoolTeam,
) -> None:
    RegionalPoolTeamManipulator.createOrUpdate(old_regional_pool_team)
    stored = none_throws(RegionalPoolTeam.get_by_id("2025_frc254"))
    assert stored.team == ndb.Key(Team, "frc254")
    assert stored.year == 2025

    RegionalPoolTeamManipulator.createOrUpdate(new_regional_pool_team)
    assert RegionalPoolTeam.query().count() == 1


@pytest.mark.usefixtures("ndb_context")
def test_findOrSpawn(
    old_regional_pool_team: RegionalPoolTeam,
    new_regional_pool_team: RegionalPoolTeam,
) -> None:
    old_regional_pool_team.put()
    merged = RegionalPoolTeamManipulator.findOrSpawn(new_regional_pool_team)
    assert merged.key_name == "2025_frc254"


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge(
    old_regional_pool_team: RegionalPoolTeam,
    new_regional_pool_team: RegionalPoolTeam,
) -> None:
    merged = RegionalPoolTeamManipulator.updateMerge(
        new_regional_pool_team, old_regional_pool_team
    )
    assert merged is old_regional_pool_team
    assert merged._updated_attrs == set()


def test_getCacheKeysAndQueries() -> None:
    cache_keys_and_queries = RegionalPoolTeamManipulator.getCacheKeysAndQueries(
        {"year": {2025}}
    )
    assert [query for _, query in cache_keys_and_queries] == [RegionalTeamsQuery]

from backend.common.models.team import Team
from backend.common.queries.team_query import TeamQuery


def test_team_not_found() -> None:
    team = TeamQuery(team_key="frc254").fetch()
    assert team is None


def test_team_is_found() -> None:
    Team(id="frc254", team_number=254).put()
    result = TeamQuery(team_key="frc254").fetch()
    assert result is not None
    assert result.team_number == 254


def test_affected_queries() -> None:
    assert {
        q.cache_key for q in TeamQuery._team_affected_queries(team_key="frc254")
    } == {TeamQuery(team_key="frc254").cache_key}

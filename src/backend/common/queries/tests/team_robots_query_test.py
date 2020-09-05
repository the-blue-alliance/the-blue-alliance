from google.cloud import ndb

from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.robot_query import TeamRobotsQuery


def test_no_data() -> None:
    robots = TeamRobotsQuery(team_key="frc254").fetch()
    assert robots == []


def test_fetch_robots() -> None:
    r = Robot(
        id="frc254_2019",
        team=ndb.Key(Team, "frc254"),
        year=2019,
    )
    r.put()

    robots = TeamRobotsQuery(team_key="frc254").fetch()
    assert robots == [r]

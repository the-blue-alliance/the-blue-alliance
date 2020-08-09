from typing import Set

from google.cloud import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import RobotKey, TeamKey, Year
from backend.common.models.team import Team


class Robot(CachedModel):
    """
    Represent a team's robot in a given year
    key_name is like <team_key>_<year> (e.g. frc1124_2015)
    """

    team = ndb.KeyProperty(kind=Team)
    year = ndb.IntegerProperty()
    robot_name = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "robot_name",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "team": set(),
            "year": set(),
        }
        super(Robot, self).__init__(*args, **kw)

    @property
    def key_name(self) -> RobotKey:
        return self.renderKeyName(self.team.id(), self.year)

    @classmethod
    def renderKeyName(cls, teamKey: TeamKey, year: Year) -> RobotKey:
        return "{}_{}".format(teamKey, year)

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and Team.validate_key_name(split[0])
            and split[1].isnumeric()
        )

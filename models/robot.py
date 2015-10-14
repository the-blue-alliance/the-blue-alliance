from google.appengine.ext import ndb

from models.team import Team


class Robot(ndb.Model):
    """
    Represent a team's robot in a given year
    key_name is like <team_key>_<year> (e.g. frc1124_2015)
    """

    team = ndb.KeyProperty(kind=Team)
    year = ndb.IntegerProperty()
    robot_name = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'team': set(),
            'year': set(),
        }
        super(Robot, self).__init__(*args, **kw)

    @property
    def key_name(self):
        return self.renderKeyName(self.team.id(), self.year)

    @classmethod
    def renderKeyName(self, teamKey, year):
        return "{}_{}".format(teamKey, year)

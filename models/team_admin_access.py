
from google.appengine.ext import ndb
from models.account import Account
from models.team import Team


class TeamAdminAccess(ndb.Model):
    """
    This class represents a pre-issued token that the TBA admins can generate
    and grant to whitelisted accounts. Accounts linked to these tokens will be
    granted moderator privileges for that team's media
    """

    # This is the team number that this code is valid for
    team_number = ndb.IntegerProperty()
    year = ndb.IntegerProperty()
    access_code = ndb.StringProperty()
    expiration = ndb.DateTimeProperty()

    account = ndb.KeyProperty(kind=Account)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    @property
    def key_name(self):
        return self.renderKeyName(self.team_number, self.year)

    @property
    def team_key(self):
        return ndb.Key(Team, "frc{}".format(self.team_number))

    @classmethod
    def renderKeyName(cls, teamNumber, year):
        return "frc{}_{}".format(teamNumber, year)

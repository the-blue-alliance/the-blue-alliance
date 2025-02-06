from google.appengine.ext import ndb

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import RegionalPoolTeamKey, TeamKey, Year
from backend.common.models.team import Team


class RegionalPoolTeam(CachedModel):
    """
    RegionalPoolTeam represents a team that competed in regionals in a season
    (and is eligible for Championship via the regional pool)

    Think of it as the regional equivalent of DistrictTeam
    """

    team = ndb.KeyProperty(kind=Team)
    year: Year = ndb.IntegerProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw) -> None:
        self._affected_references = {
            "year": set(),
        }
        super(RegionalPoolTeam, self).__init__(*args, **kw)

    @property
    def key_name(self) -> RegionalPoolTeamKey:
        return self.render_key_name(self.year, self.team.id())

    @staticmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        try:
            return (
                len(split) == 2
                and int(split[0]) in SeasonHelper.get_valid_regional_pool_years()
                and Team.validate_key_name(split[1])
            )
        except ValueError:
            return False

    @staticmethod
    def render_key_name(year: Year, team_key: TeamKey) -> str:
        return f"{year}_{team_key}"

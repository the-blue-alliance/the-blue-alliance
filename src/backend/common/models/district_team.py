from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.keys import DistrictKey, DistrictTeamKey, TeamKey, Year
from backend.common.models.team import Team


class DistrictTeam(ndb.Model):
    """
    DistrictTeam represents the "home district" for a team in a year
    key_name is like <year><district_short>_<team_key> (e.g. 2015ne_frc1124)
    district_short is one of DistrictType.type_abbrevs
    """

    team = ndb.KeyProperty(kind=Team)
    year: Year = ndb.IntegerProperty()
    # One of DistrictType constants, DEPRECATED, use district_key
    # district = (
    #    ndb.IntegerProperty()
    # )
    district_key = ndb.KeyProperty(kind=District)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "district": set(),
            "district_key": set(),
            "team": set(),
            "year": set(),
        }
        super(DistrictTeam, self).__init__(*args, **kw)

    @property
    def key_name(self) -> DistrictTeamKey:
        return self.renderKeyName(self.district_key.id(), self.team.id())

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and District.validate_key_name(split[0])
            and Team.validate_key_name(split[1])
        )

    @classmethod
    def renderKeyName(self, districtKey: DistrictKey, teamKey: TeamKey):
        return "{}_{}".format(districtKey, teamKey)

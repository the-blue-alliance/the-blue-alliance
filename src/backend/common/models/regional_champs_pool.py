from typing import List, Optional, Set

from google.appengine.ext import ndb

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import RegionalChampsPoolKey, Year
from backend.common.models.regional_pool_advancement import RegionalPoolAdvancement
from backend.common.models.regional_pool_ranking import RegionalPoolRanking


class RegionalChampsPool(CachedModel):
    """
    One instance of Championship qualification by way of the
    regional pool (2025+)
    """

    year: Year = ndb.IntegerProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    rankings: List[RegionalPoolRanking] = ndb.JsonProperty()

    # Dict of team key -> advancement data
    advancement: RegionalPoolAdvancement = ndb.JsonProperty()  # pyre-ignore[8]

    _mutable_attrs: Set[str] = {
        "rankings",
        "advancement",
    }

    def __init__(self, *args, **kw) -> None:
        self._affected_references = {
            "year": set(),
        }
        super(RegionalChampsPool, self).__init__(*args, **kw)

    @property
    def key_name(self) -> RegionalChampsPoolKey:
        return f"{self.year}"

    @classmethod
    def get_for_year(cls, year: Year) -> Optional["RegionalChampsPool"]:
        if year not in SeasonHelper.get_valid_regional_pool_years():
            return None

        return cls.get_by_id(cls.render_key_name(year))

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        try:
            year = int(key)
            return year in SeasonHelper.get_valid_regional_pool_years()
        except ValueError:
            return False

    @classmethod
    def render_key_name(cls, year: Year) -> RegionalChampsPoolKey:
        # Simply a stringified year
        return f"{year}"

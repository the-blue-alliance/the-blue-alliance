from typing import List, Literal, NamedTuple, Optional, Set, TypedDict

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import DistrictAbbreviation

LeaderboardKeyType = Literal["team", "event", "match", "team_pair"]


class InsightCategory:
    LEADERBOARD = "leaderboard"


# Helper for organizing insight names and display names
class InsightV2NameEntry(NamedTuple):
    name: str
    display_name: str


class InsightV2Names:
    BLUE_BANNERS = InsightV2NameEntry("blue_banners", "Total Blue Banners")
    MOST_MATCHES_PLAYED = InsightV2NameEntry(
        "most_matches_played", "Most Matches Played"
    )
    MOST_MATCHES_PLAYED_TOGETHER = InsightV2NameEntry(
        "most_matches_played_together", "Most Matches Played Together"
    )


class InsightV2(CachedModel):
    """
    V2 insight model. Fully typed, category-discriminated.
    Coexists with Insight (v1) until full cutover.
    key_name format: {year}_v2_{category}_{name}[_{district}]
    """

    name = ndb.StringProperty(required=True)
    display_name = ndb.StringProperty(required=True)
    year = ndb.IntegerProperty(required=True)  # 0 = all-time
    category = ndb.StringProperty(required=True, indexed=True)
    data_json = ndb.JsonProperty(required=True, indexed=False, compressed=True)
    district_abbreviation = ndb.StringProperty(required=False, indexed=True)
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _json_attrs: Set[str] = set()
    _mutable_attrs: Set[str] = {"data_json"}

    def __init__(self, *args, **kw):
        self._affected_references = {
            "name": set(),
            "year": set(),
            "category": set(),
            "district_abbreviation": set(),
        }
        super(InsightV2, self).__init__(*args, **kw)

    @property
    def data(self):
        return self.data_json

    @property
    def key_name(self) -> str:
        return self.render_key_name(
            self.year, self.category, self.name, self.district_abbreviation
        )

    @classmethod
    def render_key_name(
        cls,
        year: int,
        category: str,
        name: str,
        district_abbreviation: Optional[DistrictAbbreviation] = None,
    ) -> str:
        suffix = f"_{district_abbreviation}" if district_abbreviation else ""
        return f"{year}_v2_{category}_{name}{suffix}"


class LeaderboardRankingV2(TypedDict):
    keys: List[str] | List[List[str]]
    value: int | float


class LeaderboardDataV2(TypedDict):
    rankings: List[LeaderboardRankingV2]
    key_type: LeaderboardKeyType

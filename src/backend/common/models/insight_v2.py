from typing import List, Literal, Optional, Set, TypedDict, Union

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import DistrictAbbreviation

LeaderboardKeyType = Literal["team", "event", "match", "team_pair", "alliance"]
LeaderboardContextType = Literal["event_list", "match_alliance", "none"]

TimeseriesXType = Literal["week", "year", "event"]
TimeseriesPointContextType = Literal["none", "match_record"]


class InsightCategory:
    LEADERBOARD = "leaderboard"
    STREAK = "streak"
    TIMESERIES = "timeseries"


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


class EventListContext(TypedDict):
    event_keys: List[str]


class MatchAllianceContext(TypedDict):
    match_key: str
    alliance: List[str]  # team keys


class LeaderboardRankingWithEventList(TypedDict):
    keys: List[str]
    value: int | float
    contexts: List[
        EventListContext
    ]  # parallel to keys; zip(keys, contexts) gives per-team events


class LeaderboardRankingPairWithEventList(TypedDict):
    keys: List[List[str]]
    value: int | float
    contexts: List[EventListContext]  # parallel to keys; one context per pair


class LeaderboardRankingWithMatchAlliance(TypedDict):
    keys: List[str]  # match keys
    value: int | float
    contexts: List[MatchAllianceContext]  # parallel to keys


LeaderboardRanking = (
    LeaderboardRankingV2
    | LeaderboardRankingWithEventList
    | LeaderboardRankingPairWithEventList
    | LeaderboardRankingWithMatchAlliance
)


class LeaderboardDataV2(TypedDict):
    rankings: List[LeaderboardRanking]
    key_type: LeaderboardKeyType
    context_type: LeaderboardContextType


class StreakEntry(TypedDict):
    key: str
    key_type: LeaderboardKeyType
    streak_length: int
    start: str  # event key or year string
    end: str  # event key or year string
    is_active: bool


class StreakData(TypedDict):
    entries: List[StreakEntry]


class MatchRecordPointContext(TypedDict):
    match_key: str
    alliance: List[str]  # team keys on the record-setting alliance
    post_result_time: int  # Unix timestamp when the record was set
    is_current: bool  # True if this is still the current world record


class TimeseriesPointNoContext(TypedDict):
    x: Union[str, int, float]
    y: float


class TimeseriesPointWithMatchRecord(TypedDict):
    x: Union[str, int, float]
    y: float
    context: MatchRecordPointContext


TimeseriesPoint = Union[TimeseriesPointNoContext, TimeseriesPointWithMatchRecord]


class TimeseriesSeries(TypedDict):
    label: str
    points: List[TimeseriesPoint]


class TimeseriesData(TypedDict):
    series: List[TimeseriesSeries]
    x_type: TimeseriesXType
    x_label: str
    y_label: str
    point_context_type: TimeseriesPointContextType

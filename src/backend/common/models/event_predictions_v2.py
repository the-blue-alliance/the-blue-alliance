from typing import cast, Dict, Optional, Set, TypedDict

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import MatchKey, TeamKey


class ScoreDistribution(TypedDict):
    mean: float
    sd: float
    pmf: Dict[int, float]  # integer score -> probability


class RankingPointsPredictionPayload(TypedDict):
    expected_rp: float
    median_rp: int
    rp_pmf: Dict[int, float]
    bonus_probabilities: Dict[str, float]


class MatchPredictionV2(TypedDict):
    match_key: MatchKey
    winning_alliance: Optional[AllianceColor]
    win_probability: float  # probability for winning_alliance
    red_win_prob: float  # red win prob [0, 1]
    red: ScoreDistribution
    blue: ScoreDistribution
    ranking_points: Optional[
        Dict[str, RankingPointsPredictionPayload]
    ]  # "red", "blue" keys for Quals


class TeamRatingV2(TypedDict):
    shared_strength: float  # s
    robot_strength: float  # u
    win_rating: float  # Elo-style win rating
    pcg_rating: float  # cross-event PCG rating


class EventPredictionsV2Payload(TypedDict):
    model_version: str  # "hkf_ev_pcg_v1.0"
    as_of_match: Optional[MatchKey]
    last_updated: str  # ISO timestamp
    matches: Dict[MatchKey, MatchPredictionV2]
    team_ratings: Dict[TeamKey, TeamRatingV2]


class EventPredictionsV2(CachedModel):
    """
    Standalone SOTA predictions entity.
    Key: event_key (e.g. '2026casj')
    """

    model_version = ndb.StringProperty(required=True, default="hkf_ev_pcg_v1.0")
    as_of_match = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    # 817 KiB raw JSON compresses to ~11.5 KiB in Datastore
    predictions: EventPredictionsV2Payload = cast(
        EventPredictionsV2Payload,
        ndb.JsonProperty(compressed=True, required=True),
    )

    _mutable_attrs: Set[str] = {
        "model_version",
        "as_of_match",
        "predictions",
    }

    def __init__(self, *args, **kw):
        self._affected_references = {
            "key": set(),
        }
        super().__init__(*args, **kw)

    @property
    def key_name(self) -> str:
        return str(self.key.id())

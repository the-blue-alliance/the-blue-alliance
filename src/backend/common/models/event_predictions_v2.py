from typing import cast, Dict, Literal, Optional, Set, TypedDict

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import EventKey, MatchKey, Year


class ScorePredictionV2(TypedDict):
    mean: float
    sd: float
    p10: int
    p50: int
    p90: int


class RankingPointsPredictionV2(TypedDict):
    expected_rp: float
    median_rp: float
    win_rp_prob: float
    # Keyed by the score breakdown flag of each bonus RP (e.g. "melodyBonusAchieved").
    bonus_rp_probs: Dict[str, float]


class AlliancePredictionV2(TypedDict):
    score: ScorePredictionV2
    ranking_points: Optional[RankingPointsPredictionV2]


class MatchPredictionV2(TypedDict):
    # "pre_match": made before the match was played. "forecast": the match is unplayed.
    kind: Literal["pre_match", "forecast"]
    red_win_prob: float
    red: AlliancePredictionV2
    blue: AlliancePredictionV2


class EventPredictionsV2(CachedModel):
    """
    Match predictions of the predictions_v2 model for one event.
    key_name is the event key, like '2024casj'
    """

    model_version = ndb.StringProperty(required=True)
    # True for offseason and preseason events: the model does not learn from them.
    forecast_only = ndb.BooleanProperty(default=False)
    matches: Dict[MatchKey, MatchPredictionV2] = cast(
        Dict[MatchKey, MatchPredictionV2], ndb.JsonProperty()
    )
    # Digest of the event's matches the predictions were made from (not served). The
    # pipeline compares it with the current matches to find events with changes.
    source_fingerprint = ndb.StringProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    _mutable_attrs: Set[str] = {
        "model_version",
        "forecast_only",
        "matches",
        "source_fingerprint",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "key": set(),
        }
        super(EventPredictionsV2, self).__init__(*args, **kw)

    @property
    def key_name(self) -> EventKey:
        return str(self.key.id())

    @property
    def year(self) -> Year:
        return int(self.key_name[:4])

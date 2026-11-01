"""Inputs and outputs of the HKF match predictor."""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.keys import EventKey, MatchKey, TeamKey

# One alliance's score breakdown, as stored on a Match.
AllianceBreakdown = Mapping[str, Any]


@dataclass(frozen=True)
class MatchContext:
    """What is known about a match before it is played."""

    match_key: MatchKey
    event_key: EventKey
    event_type: EventType
    comp_level: CompLevel
    red_teams: Tuple[TeamKey, ...]
    blue_teams: Tuple[TeamKey, ...]

    @property
    def is_qual(self) -> bool:
        return self.comp_level == CompLevel.QM


@dataclass(frozen=True)
class MatchOutcome:
    """The result of a played match."""

    red_score: int
    blue_score: int
    # 1.0 for a red win, 0.0 for a blue win, 0.5 for a tie. A playoff match decided by a
    # tiebreaker counts as a win for the alliance that advanced.
    red_win: float
    red_breakdown: Optional[AllianceBreakdown] = None
    blue_breakdown: Optional[AllianceBreakdown] = None
    # Bonus ranking points earned, keyed "rp_1" .. "rp_3" (qualification matches).
    red_bonus_rps: Mapping[str, int] = field(default_factory=dict)
    blue_bonus_rps: Mapping[str, int] = field(default_factory=dict)
    red_dqs: Tuple[TeamKey, ...] = ()
    blue_dqs: Tuple[TeamKey, ...] = ()

    @property
    def has_breakdown(self) -> bool:
        return self.red_breakdown is not None or self.blue_breakdown is not None


@dataclass(frozen=True, eq=False)
class ScoreDistribution:
    """Distribution of one alliance's score: probs[k] = P(score == k)."""

    probs: np.ndarray

    @property
    def mean(self) -> float:
        return float(self.probs @ np.arange(len(self.probs)))

    @property
    def sd(self) -> float:
        k = np.arange(len(self.probs), dtype=float)
        m = self.mean
        return math.sqrt(max(float(self.probs @ ((k - m) ** 2)), 0.0))

    def prob(self, score: int) -> float:
        return float(self.probs[score]) if 0 <= score < len(self.probs) else 0.0

    def quantile(self, q: float) -> int:
        """Smallest score whose CDF reaches q."""
        cdf = np.cumsum(self.probs)
        return min(int(np.searchsorted(cdf, q - 1e-12)), len(self.probs) - 1)


@dataclass(frozen=True)
class RankingPointsPrediction:
    """Ranking points of one alliance in a qualification match."""

    expected_rp: float
    win_rp_prob: float
    bonus_rp_probs: Dict[str, float]
    max_rp: float
    median_rp: float


@dataclass(frozen=True)
class MatchPrediction:
    red_win_prob: float
    red_score: ScoreDistribution
    blue_score: ScoreDistribution
    red_rp: Optional[RankingPointsPrediction] = None
    blue_rp: Optional[RankingPointsPrediction] = None

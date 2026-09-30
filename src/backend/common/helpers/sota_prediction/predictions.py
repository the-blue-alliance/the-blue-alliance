"""Prediction output containers for FRC match forecasting models.

Provides standardized containers for:
- ScorePrediction: Generalized alliance score prediction supporting single
  point estimates or discrete probability distributions (PMF).
- RankingPointsPrediction: Ranking points forecasts including win and bonus RP probabilities.
- MatchPrediction: Complete match forecast wrapping win probabilities, scores, and RPs.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class PMF(Mapping[int, float]):
    """Compact, array-backed discrete Probability Mass Function (PMF).

    Stores probabilities over a contiguous integer score support [offset, offset + len(probs) - 1]
    as a dense 1D NumPy array. Implements the standard Python Mapping[int, float] interface,
    providing dict-like lookups, hashing, and iteration while reducing memory usage by 10x and
    enabling vectorized probability metrics (RPS, NLL).
    """

    __slots__ = ("_offset", "_probs")

    def __init__(
        self,
        offset: int,
        probs: Union[Sequence[float], np.ndarray],
        validate: bool = True,
    ) -> None:
        if isinstance(offset, bool) or not isinstance(offset, (int, np.integer)):
            raise TypeError(f"offset must be an integer, got {type(offset).__name__}")
        self._offset: int = int(offset)

        p_arr = np.asarray(probs, dtype=np.float64)
        if p_arr.ndim != 1:
            raise ValueError(
                f"probs must be a 1D sequence or array, got ndim={p_arr.ndim}"
            )
        if len(p_arr) == 0:
            raise ValueError("probs cannot be empty")

        if validate:
            if not np.all(np.isfinite(p_arr)):
                raise ValueError(
                    "PMF probabilities must be finite numbers (no NaN or Inf)"
                )
            if np.any(p_arr < 0.0):
                raise ValueError("PMF probabilities must be non-negative")
            total = float(np.sum(p_arr))
            if abs(total - 1.0) > 1e-5:
                raise ValueError(
                    f"PMF probabilities must sum to 1.0 (within 1e-5 tolerance), got {total}"
                )
            if total <= 0.0:
                raise ValueError("PMF probability sum must be positive")
            p_arr = p_arr / total

        self._probs: np.ndarray = p_arr

    @property
    def offset(self) -> int:
        """Minimum integer score in support."""
        return self._offset

    @property
    def probs(self) -> np.ndarray:
        """Contiguous probability array."""
        return self._probs

    @property
    def min_score(self) -> int:
        """Minimum integer score in support (alias for offset)."""
        return self._offset

    @property
    def max_score(self) -> int:
        """Maximum integer score in support."""
        return self._offset + len(self._probs) - 1

    @property
    def support(self) -> Tuple[int, int]:
        """Tuple of (min_score, max_score) representing the integer support bounds."""
        return self._offset, self.max_score

    # -- Mapping Interface ----------------------------------------------------

    def __getitem__(self, key: int) -> float:
        if isinstance(key, bool) or not isinstance(key, (int, np.integer)):
            raise KeyError(key)
        idx = int(key) - self._offset
        if 0 <= idx < len(self._probs):
            return float(self._probs[idx])
        raise KeyError(key)

    def __iter__(self) -> Iterator[int]:
        for i in range(len(self._probs)):
            yield self._offset + i

    def __len__(self) -> int:
        return len(self._probs)

    def get(self, key: int, default: float = 0.0) -> float:  # type: ignore[override]
        if isinstance(key, bool) or not isinstance(key, (int, np.integer)):
            return float(default)
        idx = int(key) - self._offset
        if 0 <= idx < len(self._probs):
            return float(self._probs[idx])
        return float(default)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, bool) or not isinstance(key, (int, np.integer)):
            return False
        return 0 <= (int(key) - self._offset) < len(self._probs)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PMF):
            return self._offset == other._offset and np.array_equal(
                self._probs, other._probs
            )
        if isinstance(other, Mapping):
            if len(self) != len(other):
                return False
            return all(
                k in other and math.isclose(self[k], other[k], abs_tol=1e-9)
                for k in self
            )
        return False

    def __repr__(self) -> str:
        return (
            f"PMF(offset={self._offset}, support=[{self.min_score}..{self.max_score}], "
            f"ev={self.expected_value():.2f})"
        )

    # -- Statistical Methods --------------------------------------------------

    def expected_value(self) -> float:
        """Calculate expected value E[Score] = sum(k * P(Score = k))."""
        n = len(self._probs)
        return float(self._offset) + float(
            np.dot(np.arange(n, dtype=np.float64), self._probs)
        )

    def mode(self) -> int:
        """Return the integer score with the maximum probability."""
        return int(self._offset + int(np.argmax(self._probs)))

    def prob(self, score: int) -> float:
        """Return the predicted probability P(Score = score)."""
        idx = int(score) - self._offset
        if 0 <= idx < len(self._probs):
            return float(self._probs[idx])
        return 0.0

    def cdf(self, score: int) -> float:
        """Return cumulative probability P(Score <= score)."""
        idx = int(score) - self._offset
        if idx < 0:
            return 0.0
        if idx >= len(self._probs):
            return 1.0
        return float(np.sum(self._probs[: idx + 1]))

    def to_dict(self) -> Dict[int, float]:
        """Convert container to standard Python dict mapping score to float probability."""
        return {int(self._offset + i): float(p) for i, p in enumerate(self._probs)}

    def to_array(self) -> np.ndarray:
        """Return a copy of the probability array."""
        return self._probs.copy()

    # -- Factory Constructors -------------------------------------------------

    @classmethod
    def from_array(
        cls,
        probs: Union[Sequence[float], np.ndarray],
        offset: int = 0,
        validate: bool = True,
    ) -> PMF:
        """Construct a PMF directly from a probability array and offset."""
        return cls(offset=offset, probs=probs, validate=validate)

    @classmethod
    def from_dict(cls, d: Mapping[int, float], validate: bool = True) -> PMF:
        """Construct a PMF from a dictionary or Mapping of {score: probability}."""
        if not isinstance(d, Mapping):
            raise TypeError(f"pmf must be a dict or Mapping, got {type(d).__name__}")
        if not d:
            raise ValueError("pmf dictionary cannot be empty when provided")

        clean_items: List[Tuple[int, float]] = []
        total_prob = 0.0
        for k, p in d.items():
            if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or k < 0:
                raise ValueError(
                    f"PMF score key must be a non-negative integer, got {k!r}"
                )
            if (
                isinstance(p, bool)
                or not isinstance(p, (int, float, np.floating))
                or not math.isfinite(p)
                or p < 0.0
            ):
                raise ValueError(
                    f"PMF probability must be a non-negative finite number, got {p!r} for score {k}"
                )
            val_p = float(p)
            clean_items.append((int(k), val_p))
            total_prob += val_p

        if validate:
            if abs(total_prob - 1.0) > 1e-5:
                raise ValueError(
                    f"PMF probabilities must sum to 1.0 (within 1e-5 tolerance), got {total_prob}"
                )
            if total_prob <= 0.0:
                raise ValueError("PMF probability sum must be positive")

        min_k = min(k for k, _ in clean_items)
        max_k = max(k for k, _ in clean_items)
        size = max_k - min_k + 1
        probs = np.zeros(size, dtype=np.float64)

        norm_factor = total_prob if validate and total_prob > 0.0 else 1.0
        for k, p in clean_items:
            probs[k - min_k] += p / norm_factor

        return cls(offset=min_k, probs=probs, validate=False)


@dataclass
class ScorePrediction:
    """Generalized alliance score prediction container.

    Supports both single deterministic point estimates (integer or float) and
    full discrete probability mass functions (PMF) over non-negative integer scores.
    """

    point_estimate: Optional[float] = None
    pmf: Optional[PMF] = None

    def __post_init__(self) -> None:
        if self.point_estimate is None and self.pmf is None:
            raise ValueError(
                "ScorePrediction must have at least one of point_estimate or pmf."
            )

        if self.point_estimate is not None:
            if isinstance(self.point_estimate, bool) or not isinstance(
                self.point_estimate, (int, float)
            ):
                raise TypeError(
                    f"point_estimate must be a numeric type, got {type(self.point_estimate).__name__}"
                )
            if not math.isfinite(self.point_estimate) or self.point_estimate < 0.0:
                raise ValueError(
                    f"point_estimate must be a non-negative finite number, got {self.point_estimate}"
                )
            self.point_estimate = float(self.point_estimate)

        if self.pmf is not None:
            if isinstance(self.pmf, PMF):
                pass
            elif isinstance(self.pmf, Mapping):
                self.pmf = PMF.from_dict(self.pmf)
            else:
                raise TypeError(
                    f"pmf must be a dict or PMF, got {type(self.pmf).__name__}"
                )

    def expected_value(self) -> float:
        """Calculate the expected value or explicit point readout of the score prediction.

        If point_estimate is explicitly provided, returns float(point_estimate).
        Otherwise if a PMF is provided, returns sum(k * p).
        """
        if self.point_estimate is not None:
            return float(self.point_estimate)
        if self.pmf is not None:
            return self.pmf.expected_value()
        raise ValueError("ScorePrediction has neither point_estimate nor pmf.")

    @property
    def mean(self) -> float:
        """Alias for expected_value()."""
        return self.expected_value()

    def mode(self) -> int:
        """Return the most likely integer score.

        If a PMF is provided, returns the score with maximum probability.
        Otherwise returns round(point_estimate).
        """
        if self.pmf is not None:
            return self.pmf.mode()
        assert self.point_estimate is not None
        return round(self.point_estimate)

    def prob(self, score: int) -> float:
        """Return the predicted probability of the exact integer score."""
        if self.pmf is not None:
            return self.pmf.prob(score)
        assert self.point_estimate is not None
        return 1.0 if score == round(self.point_estimate) else 0.0

    def cdf(self, score: int) -> float:
        """Return the cumulative probability P(Score <= score)."""
        if self.pmf is not None:
            return self.pmf.cdf(score)
        assert self.point_estimate is not None
        return 1.0 if score >= round(self.point_estimate) else 0.0

    @property
    def has_pmf(self) -> bool:
        """Return True if PMF is populated."""
        return self.pmf is not None

    def is_distribution(self) -> bool:
        """Return True if this prediction provides a probability distribution."""
        return self.pmf is not None

    @classmethod
    def from_point(cls, score: float) -> ScorePrediction:
        """Factory method to construct a ScorePrediction from a single point estimate."""
        return cls(point_estimate=float(score))

    @classmethod
    def from_pmf(
        cls,
        pmf: Union[Mapping[int, float], PMF],
        point_estimate: Optional[float] = None,
        validate: bool = True,
    ) -> ScorePrediction:
        """Factory method to construct a ScorePrediction from a PMF."""
        if isinstance(pmf, PMF):
            pmf_obj = pmf
        elif isinstance(pmf, Mapping):
            pmf_obj = PMF.from_dict(pmf, validate=validate)
        else:
            raise TypeError(f"pmf must be a dict or PMF, got {type(pmf).__name__}")

        if not validate:
            obj = object.__new__(cls)
            obj.point_estimate = (
                float(point_estimate) if point_estimate is not None else None
            )
            obj.pmf = pmf_obj
            return obj
        return cls(point_estimate=point_estimate, pmf=pmf_obj)

    def to_dict(self) -> Dict[str, Any]:
        """Convert container to a JSON-serializable dictionary."""
        return {
            "point_estimate": self.point_estimate,
            "pmf": self.pmf.to_dict() if self.pmf is not None else None,
            "expected_value": self.expected_value(),
            "is_distribution": self.is_distribution(),
        }


@dataclass
class RankingPointsPrediction:
    """Predicted ranking points container for qualification matches.

    Supports total expected ranking points and optional component-level probabilities
    (Win RP probability, bonus RP probabilities).

    ``expected_rp`` is the mean of the predicted RP distribution. The benchmark
    uses it for RP RMSE. It must stay calibrated as a mean.

    ``median_rp`` is optional. It is a point that minimizes expected absolute
    error, for example the median of the model's RP distribution. It may differ
    from ``expected_rp``. When it is present, the benchmark uses it for RP MAE
    and reports the gap to ``expected_rp``. When it is absent, the benchmark
    uses ``expected_rp`` for RP MAE.
    """

    expected_rp: Optional[float] = None
    win_rp_prob: Optional[float] = None
    bonus_rp_probs: Optional[Dict[str, float]] = None
    rp_probabilities: Optional[Dict[str, float]] = None

    max_rp: Optional[float] = None
    median_rp: Optional[float] = None

    def __post_init__(self) -> None:
        # Cross-populate from rp_probabilities dictionary if provided
        if self.rp_probabilities is not None:
            if not isinstance(self.rp_probabilities, dict):
                raise TypeError(
                    f"rp_probabilities must be a dict, got {type(self.rp_probabilities).__name__}"
                )
            for k, v in self.rp_probabilities.items():
                if (
                    isinstance(v, bool)
                    or not isinstance(v, (int, float))
                    or not math.isfinite(v)
                    or not (0.0 <= v <= 1.0)
                ):
                    raise ValueError(
                        f"RP probability for {k!r} must be in [0.0, 1.0], got {v}"
                    )
            if self.win_rp_prob is None and "win" in self.rp_probabilities:
                self.win_rp_prob = float(self.rp_probabilities["win"])
            if self.bonus_rp_probs is None:
                self.bonus_rp_probs = {
                    k: float(v) for k, v in self.rp_probabilities.items() if k != "win"
                }

        if self.win_rp_prob is not None:
            if (
                isinstance(self.win_rp_prob, bool)
                or not isinstance(self.win_rp_prob, (int, float))
                or not math.isfinite(self.win_rp_prob)
                or not (0.0 <= self.win_rp_prob <= 1.0)
            ):
                raise ValueError(
                    f"win_rp_prob must be a finite number in [0.0, 1.0], got {self.win_rp_prob}"
                )
            self.win_rp_prob = float(self.win_rp_prob)

        if self.bonus_rp_probs is not None:
            if not isinstance(self.bonus_rp_probs, dict):
                raise TypeError(
                    f"bonus_rp_probs must be a dict, got {type(self.bonus_rp_probs).__name__}"
                )
            clean_bonuses: Dict[str, float] = {}
            for k, v in self.bonus_rp_probs.items():
                if not isinstance(k, str):
                    raise TypeError(f"bonus RP key must be a string, got {k!r}")
                if (
                    isinstance(v, bool)
                    or not isinstance(v, (int, float))
                    or not math.isfinite(v)
                    or not (0.0 <= v <= 1.0)
                ):
                    raise ValueError(
                        f"bonus RP probability for {k!r} must be in [0.0, 1.0], got {v}"
                    )
                clean_bonuses[k] = float(v)
            self.bonus_rp_probs = clean_bonuses

        # Determine maximum valid RP bound (4.0 for standard games, 6.0 for 2025+ with 3 bonus RPs)
        upper_limit = 4.0
        if self.max_rp is not None:
            upper_limit = float(self.max_rp)
        elif self.bonus_rp_probs is not None and len(self.bonus_rp_probs) >= 3:
            upper_limit = 6.0

        # Auto-compute expected_rp if not explicitly provided
        if self.expected_rp is None:
            if self.win_rp_prob is not None or self.bonus_rp_probs is not None:
                win_val = 3.0 if upper_limit > 4.0 else 2.0
                win_contrib = win_val * (self.win_rp_prob or 0.0)
                bonus_contrib = (
                    sum(self.bonus_rp_probs.values()) if self.bonus_rp_probs else 0.0
                )
                self.expected_rp = min(
                    upper_limit, max(0.0, win_contrib + bonus_contrib)
                )
            else:
                raise ValueError(
                    "RankingPointsPrediction requires expected_rp or win/bonus RP probabilities."
                )
        else:
            if (
                isinstance(self.expected_rp, bool)
                or not isinstance(self.expected_rp, (int, float))
                or not math.isfinite(self.expected_rp)
                or not (0.0 <= self.expected_rp <= upper_limit)
            ):
                raise ValueError(
                    f"expected_rp must be a finite number in [0.0, {upper_limit:.1f}], got {self.expected_rp}"
                )
            self.expected_rp = float(self.expected_rp)

        if self.median_rp is not None:
            if (
                isinstance(self.median_rp, bool)
                or not isinstance(self.median_rp, (int, float))
                or not math.isfinite(self.median_rp)
                or not (0.0 <= self.median_rp <= upper_limit)
            ):
                raise ValueError(
                    f"median_rp must be a finite number in [0.0, {upper_limit:.1f}], got {self.median_rp}"
                )
            self.median_rp = float(self.median_rp)

    @property
    def total_expected_rp(self) -> float:
        """Alias for expected_rp."""
        assert self.expected_rp is not None
        return self.expected_rp

    @property
    def mae_point(self) -> float:
        """Return the point that the benchmark scores with RP MAE.

        This is ``median_rp`` when the model reports it, else ``expected_rp``.
        """
        if self.median_rp is not None:
            return self.median_rp
        assert self.expected_rp is not None
        return self.expected_rp

    def to_dict(self) -> Dict[str, Any]:
        """Convert container to a JSON-serializable dictionary."""
        out: Dict[str, Any] = {
            "expected_rp": self.expected_rp,
            "win_rp_prob": self.win_rp_prob,
            "bonus_rp_probs": self.bonus_rp_probs,
        }
        if self.median_rp is not None:
            out["median_rp"] = self.median_rp
        return out


@dataclass
class MatchPrediction:
    """Standardized prediction output container returned by BasePredictor.predict_match.

    Wraps win probabilities, alliance score predictions, and ranking points.
    """

    red_win_prob: float
    red_score: ScorePrediction
    blue_score: ScorePrediction
    red_rp: Optional[RankingPointsPrediction] = None
    blue_rp: Optional[RankingPointsPrediction] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.red_win_prob, bool) or not isinstance(
            self.red_win_prob, (int, float)
        ):
            raise TypeError(
                f"red_win_prob must be a numeric type, got {type(self.red_win_prob).__name__}"
            )
        if not math.isfinite(self.red_win_prob) or not (
            0.0 <= self.red_win_prob <= 1.0
        ):
            raise ValueError(
                f"red_win_prob must be a finite float in [0.0, 1.0], got {self.red_win_prob}"
            )
        self.red_win_prob = float(self.red_win_prob)

        # Automatic coercion for scores
        if isinstance(self.red_score, (int, float)) and not isinstance(
            self.red_score, bool
        ):
            self.red_score = ScorePrediction.from_point(float(self.red_score))
        elif isinstance(self.red_score, (dict, PMF)):
            self.red_score = ScorePrediction.from_pmf(self.red_score)
        elif not isinstance(self.red_score, ScorePrediction):
            raise TypeError(
                f"red_score must be a ScorePrediction instance, got {type(self.red_score).__name__}"
            )

        if isinstance(self.blue_score, (int, float)) and not isinstance(
            self.blue_score, bool
        ):
            self.blue_score = ScorePrediction.from_point(float(self.blue_score))
        elif isinstance(self.blue_score, (dict, PMF)):
            self.blue_score = ScorePrediction.from_pmf(self.blue_score)
        elif not isinstance(self.blue_score, ScorePrediction):
            raise TypeError(
                f"blue_score must be a ScorePrediction instance, got {type(self.blue_score).__name__}"
            )

        # Automatic coercion for ranking points
        if isinstance(self.red_rp, (int, float)) and not isinstance(self.red_rp, bool):
            self.red_rp = RankingPointsPrediction(expected_rp=float(self.red_rp))
        elif isinstance(self.red_rp, dict):
            self.red_rp = RankingPointsPrediction(bonus_rp_probs=self.red_rp)
        elif self.red_rp is not None and not isinstance(
            self.red_rp, RankingPointsPrediction
        ):
            raise TypeError(
                f"red_rp must be a RankingPointsPrediction instance, got {type(self.red_rp).__name__}"
            )

        if isinstance(self.blue_rp, (int, float)) and not isinstance(
            self.blue_rp, bool
        ):
            self.blue_rp = RankingPointsPrediction(expected_rp=float(self.blue_rp))
        elif isinstance(self.blue_rp, dict):
            self.blue_rp = RankingPointsPrediction(bonus_rp_probs=self.blue_rp)
        elif self.blue_rp is not None and not isinstance(
            self.blue_rp, RankingPointsPrediction
        ):
            raise TypeError(
                f"blue_rp must be a RankingPointsPrediction instance, got {type(self.blue_rp).__name__}"
            )

    @property
    def red(self) -> ScorePrediction:
        """Alias for red_score."""
        return self.red_score

    @property
    def blue(self) -> ScorePrediction:
        """Alias for blue_score."""
        return self.blue_score

    @property
    def blue_win_prob(self) -> float:
        """Derived Blue win probability: P(Blue win) = 1.0 - P(Red win)."""
        return 1.0 - self.red_win_prob

    @property
    def predicted_winner(self) -> Optional[str]:
        """Categorical predicted winner: 'red' if p > 0.5, 'blue' if p < 0.5, None if tie (p == 0.5)."""
        if self.red_win_prob > 0.5:
            return "red"
        elif self.red_win_prob < 0.5:
            return "blue"
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert container to a JSON-serializable dictionary."""
        return {
            "red_win_prob": self.red_win_prob,
            "blue_win_prob": self.blue_win_prob,
            "predicted_winner": self.predicted_winner,
            "red_score": self.red_score.to_dict(),
            "blue_score": self.blue_score.to_dict(),
            "red_rp": self.red_rp.to_dict() if self.red_rp else None,
            "blue_rp": self.blue_rp.to_dict() if self.blue_rp else None,
            "metadata": dict(self.metadata),
        }

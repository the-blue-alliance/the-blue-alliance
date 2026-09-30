"""Pre-match context container and temporal violation guards.

Defines:
- `TemporalViolationError`: Exception raised when code attempts to access post-match
  outcome information on pre-match containers.
- `MatchContext`: Frozen immutable pre-match dataclass containing strictly pre-match
  information (teams, schedule, event metadata). Accessing scores, winner, or
  breakdowns raises `TemporalViolationError`.
- `FrozenDict`: Immutable dictionary protecting event and match metadata.
- `MatchOutcome`: Re-exported from `outcome.py` for comprehensive access.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence, Tuple

COMP_LEVEL_ORDER: Dict[str, int] = {
    "qm": 1,
    "ef": 2,
    "qf": 3,
    "sf": 4,
    "f": 5,
}


class TemporalViolationError(AttributeError, KeyError):
    """Raised when an algorithm attempts to access post-match outcome data during pre-match prediction.

    Inherits from both AttributeError and KeyError to intercept dot notation
    (`context.red_score`), dictionary item lookup (`context['red_score']`),
    and `.get('red_score')` queries.
    """

    pass


FORBIDDEN_ATTRIBUTES: frozenset[str] = frozenset(
    {
        # Score fields
        "score",
        "scores",
        "red_score",
        "blue_score",
        "score_breakdown",
        "breakdown",
        "alliance_scores",
        # Winner, tie, and match result fields
        "winner",
        "actual_winner",
        "winning_alliance",
        "outcome",
        "result",
        "results",
        "win_target",
        "actual_red_win",
        "actual_blue_win",
        "actual_red_outcome",
        "actual_blue_outcome",
        "red_outcome",
        "blue_outcome",
        "is_tie",
        "tie",
        # Ranking points and bonus points
        "rp",
        "ranking_points",
        "ranking_point",
        "red_rp",
        "blue_rp",
        "red_rp_earned",
        "blue_rp_earned",
        "rp_earned",
        "tba_rpEarned",
        "tba_rpearned",
        "bonus_rp",
        "bonus_rps",
        "red_bonus_rps",
        "blue_bonus_rps",
        # Disqualification fields
        "red_dqs",
        "blue_dqs",
        "dq_team_keys",
        # Raw alliance container and match status
        "alliances",
        "is_played",
        "post_result_time",
    }
)

_FORBIDDEN_LOWER: frozenset[str] = frozenset(k.lower() for k in FORBIDDEN_ATTRIBUTES)


def _is_forbidden_attr(key: Any) -> bool:
    """Return True if key represents a forbidden post-match outcome attribute.

    Performs case-insensitive inspection and safely handles non-string keys.
    """
    if isinstance(key, str):
        return key in FORBIDDEN_ATTRIBUTES or key.lower() in _FORBIDDEN_LOWER
    return False


def _make_hashable(val: Any) -> Any:
    """Recursively convert nested dictionaries, lists, and sets to hashable, deterministic structures."""
    if isinstance(val, (dict, Mapping)):
        return tuple(
            sorted(
                ((k, _make_hashable(v)) for k, v in val.items()),
                key=lambda item: (type(item[0]).__name__, str(item[0])),
            )
        )
    if isinstance(val, (list, tuple)):
        return tuple(_make_hashable(item) for item in val)
    if isinstance(val, (set, frozenset)):
        return tuple(
            sorted(
                (_make_hashable(item) for item in val),
                key=lambda item: (type(item).__name__, str(item)),
            )
        )
    return val


def _deep_freeze(obj: Any) -> Any:
    """Recursively freeze dictionaries to FrozenDict and lists/sets to tuples.

    Primitives, strings, and already-immutable types are returned unchanged.
    Ensures nested objects cannot be mutated and share no mutable references
    with external callers.
    """
    if isinstance(obj, Mapping):
        return FrozenDict({k: _deep_freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple, set, frozenset)):
        return tuple(_deep_freeze(item) for item in obj)
    return obj


class FrozenDict(dict):
    """An immutable dictionary that rejects item mutations to protect metadata."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for k, v in list(self.items()):
            if isinstance(v, Mapping) and not isinstance(v, FrozenDict):
                super().__setitem__(k, _deep_freeze(v))
            elif isinstance(v, (list, set, frozenset)):
                super().__setitem__(k, _deep_freeze(v))

    def __setitem__(self, key: Any, value: Any) -> None:
        raise TypeError(
            f"'{type(self).__name__}' object does not support item assignment"
        )

    def __delitem__(self, key: Any) -> None:
        raise TypeError(
            f"'{type(self).__name__}' object does not support item deletion"
        )

    def clear(self) -> None:
        raise TypeError(f"'{type(self).__name__}' object does not support mutation")

    def pop(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError(f"'{type(self).__name__}' object does not support mutation")

    def popitem(self) -> Any:
        raise TypeError(f"'{type(self).__name__}' object does not support mutation")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(f"'{type(self).__name__}' object does not support mutation")

    def setdefault(self, key: Any, default: Any = None) -> Any:
        raise TypeError(f"'{type(self).__name__}' object does not support mutation")

    def __ior__(self, other: Any) -> FrozenDict:
        raise TypeError(
            f"'{type(self).__name__}' object does not support in-place mutation"
        )

    def __or__(self, other: Any) -> FrozenDict:
        if isinstance(other, (dict, Mapping)):
            combined = dict(self)
            combined.update(other)
            return FrozenDict(combined)
        return NotImplemented

    def __ror__(self, other: Any) -> FrozenDict:
        if isinstance(other, (dict, Mapping)):
            combined = dict(other)
            combined.update(self)
            return FrozenDict(combined)
        return NotImplemented

    def __copy__(self) -> FrozenDict:
        """Shallow copy returns self since FrozenDict is immutable."""
        return self

    def __deepcopy__(self, memo: Optional[Dict[int, Any]] = None) -> FrozenDict:
        """Deep copy reconstructs nested elements while preserving FrozenDict immutability."""
        if memo is None:
            memo = {}
        d = id(self)
        if d in memo:
            return memo[d]
        res = self.__class__()
        memo[d] = res
        for k, v in self.items():
            super(FrozenDict, res).__setitem__(
                copy.deepcopy(k, memo),
                copy.deepcopy(v, memo),
            )
        return res

    def __reduce__(self) -> Tuple[type, Tuple[Dict[Any, Any]]]:
        """Support serialization/pickling by reconstructing via class callable and dict payload."""
        return (self.__class__, (dict(self),))

    def __hash__(self) -> int:
        """Compute a deterministic hash from a frozen recursive representation."""
        cached = self.__dict__.get("_hash")
        if cached is None:
            cached = hash(_make_hashable(self))
            self.__dict__["_hash"] = cached
        return cached


@dataclass(frozen=True, init=False)
class MatchContext:
    """Immutable, temporal-firewalled pre-match context for prediction models.

    Contains exclusively information known before the match commences:
    - Match and tournament identifiers (`match_key`, `event_key`, `comp_level`, `set_number`, `match_number`)
    - Timing fields (`scheduled_time`, `actual_time`)
    - Alliance team rosters (`red_teams`, `blue_teams`, `red_surrogates`, `blue_surrogates`)
    - Event metadata (`event_metadata` dict with year, week, event_type, etc.)

    Guarantees:
    - Immutable: Any attempt to mutate fields raises `FrozenInstanceError` or `AttributeError`.
    - Inner container protection: Team lists are stored as immutable tuples; `event_metadata` is stored in a `FrozenDict`.
    - Anti-lookahead guards: Any attempt to access, look up, or check `red_score`, `blue_score`,
      `winning_alliance`, `score_breakdown`, `winner`, `outcome`, `red_rp`, `blue_rp`,
      `red_dqs`, `blue_dqs`, or `dq_team_keys`
      via dot notation, dict lookup, `.get()`, or `in` operator raises `TemporalViolationError`.
    """

    match_key: str
    event_key: str
    comp_level: str
    set_number: int
    match_number: int
    red_teams: Tuple[str, ...]
    blue_teams: Tuple[str, ...]
    scheduled_time: Optional[int] = None
    actual_time: Optional[int] = None
    event_metadata: Dict[str, Any] = field(default_factory=dict)
    red_surrogates: Tuple[str, ...] = ()
    blue_surrogates: Tuple[str, ...] = ()

    def __init__(
        self,
        match_key: str,
        event_key: str,
        comp_level: str,
        set_number: int,
        match_number: int,
        red_teams: Sequence[str],
        blue_teams: Sequence[str],
        scheduled_time: Optional[int] = None,
        actual_time: Optional[int] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        red_surrogates: Sequence[str] = (),
        blue_surrogates: Sequence[str] = (),
        **extra_kwargs: Any,
    ) -> None:
        """Initialize MatchContext, enforcing strict isolation from outcome data."""
        for k in extra_kwargs:
            if _is_forbidden_attr(k):
                raise TemporalViolationError(
                    f"Temporal violation: Cannot initialize MatchContext with outcome attribute '{k}'. "
                    f"Outcome data is accessible only in model.update() via MatchOutcome."
                )
            raise TypeError(
                f"MatchContext.__init__() got an unexpected keyword argument '{k}'"
            )

        object.__setattr__(self, "match_key", str(match_key))
        object.__setattr__(self, "event_key", str(event_key))
        object.__setattr__(self, "comp_level", str(comp_level))
        object.__setattr__(self, "set_number", int(set_number))
        object.__setattr__(self, "match_number", int(match_number))
        object.__setattr__(self, "red_teams", tuple(str(t) for t in red_teams))
        object.__setattr__(self, "blue_teams", tuple(str(t) for t in blue_teams))
        object.__setattr__(
            self,
            "scheduled_time",
            int(scheduled_time) if scheduled_time is not None else None,
        )
        object.__setattr__(
            self, "actual_time", int(actual_time) if actual_time is not None else None
        )
        object.__setattr__(self, "event_metadata", _deep_freeze(event_metadata or {}))
        object.__setattr__(
            self, "red_surrogates", tuple(str(t) for t in red_surrogates)
        )
        object.__setattr__(
            self, "blue_surrogates", tuple(str(t) for t in blue_surrogates)
        )
        self.__post_init__()

    def __post_init__(self) -> None:
        """Post-initialization validation and recursive deep freezing of metadata."""
        object.__setattr__(
            self,
            "event_metadata",
            _deep_freeze(getattr(self, "event_metadata", None) or {}),
        )
        object.__setattr__(
            self, "red_teams", tuple(str(t) for t in getattr(self, "red_teams", ()))
        )
        object.__setattr__(
            self, "blue_teams", tuple(str(t) for t in getattr(self, "blue_teams", ()))
        )
        object.__setattr__(
            self,
            "red_surrogates",
            tuple(str(t) for t in getattr(self, "red_surrogates", ())),
        )
        object.__setattr__(
            self,
            "blue_surrogates",
            tuple(str(t) for t in getattr(self, "blue_surrogates", ())),
        )

    def __getattr__(self, name: str) -> Any:
        """Intercept dot attribute access; raise TemporalViolationError on forbidden attributes."""
        if _is_forbidden_attr(name):
            raise TemporalViolationError(
                f"Temporal violation: Attribute '{name}' represents post-match outcome data and "
                f"is strictly prohibited on MatchContext '{self.match_key}'. "
                f"Outcome data is accessible only in model.update() via MatchOutcome."
            )
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, item: Any) -> Any:
        """Intercept dict-style item access; raise TemporalViolationError on forbidden keys."""
        if _is_forbidden_attr(item):
            raise TemporalViolationError(
                f"Temporal violation: Key '{item}' represents post-match outcome data and "
                f"is strictly prohibited on MatchContext '{self.match_key}'. "
                f"Outcome data is accessible only in model.update() via MatchOutcome."
            )
        if isinstance(item, str) and hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: Any, default: Any = None) -> Any:
        """Allow dict-style .get(); raise TemporalViolationError on forbidden keys."""
        if _is_forbidden_attr(item):
            raise TemporalViolationError(
                f"Temporal violation: Key '{item}' represents post-match outcome data and "
                f"is strictly prohibited on MatchContext '{self.match_key}'."
            )
        if isinstance(item, str) and hasattr(self, item):
            return getattr(self, item)
        return default

    def __contains__(self, item: Any) -> bool:
        """Intercept membership checks; raise TemporalViolationError on forbidden keys."""
        if _is_forbidden_attr(item):
            raise TemporalViolationError(
                f"Temporal violation: Probing existence of outcome attribute '{item}' "
                f"is strictly prohibited on MatchContext '{self.match_key}'."
            )
        if isinstance(item, str):
            return hasattr(self, item)
        return False

    @property
    def key(self) -> str:
        """Match key alias for parity with TBAMatch."""
        return self.match_key

    @property
    def time(self) -> Optional[int]:
        """Scheduled match timestamp alias for parity with TBAMatch."""
        return self.scheduled_time

    @property
    def effective_start_time(self) -> Optional[int]:
        """Effective match start time: actual_time, falling back to scheduled_time."""
        return self.actual_time if self.actual_time is not None else self.scheduled_time

    @property
    def is_qualification(self) -> bool:
        """Return True if match is a qualification match ('qm')."""
        return self.comp_level == "qm"

    @property
    def is_playoff(self) -> bool:
        """Return True if match is a playoff/elimination match ('ef', 'qf', 'sf', 'f')."""
        return self.comp_level in ("ef", "qf", "sf", "f")

    @property
    def comp_level_rank(self) -> int:
        """Numerical progression rank for comp_level (qm=1, ef=2, qf=3, sf=4, f=5)."""
        return COMP_LEVEL_ORDER.get(self.comp_level, 99)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pre-match attributes to a plain dictionary.

        Guaranteed to contain zero post-match outcome fields.
        """
        return {
            "match_key": self.match_key,
            "event_key": self.event_key,
            "comp_level": self.comp_level,
            "set_number": self.set_number,
            "match_number": self.match_number,
            "scheduled_time": self.scheduled_time,
            "actual_time": self.actual_time,
            "red_teams": list(self.red_teams),
            "blue_teams": list(self.blue_teams),
            "event_metadata": dict(self.event_metadata),
            "red_surrogates": list(self.red_surrogates),
            "blue_surrogates": list(self.blue_surrogates),
        }

    @classmethod
    def from_tba_match(
        cls,
        match: Any,
        event: Optional[Any] = None,
    ) -> MatchContext:
        """Factory creating an immutable MatchContext from a TBAMatch and optional TBAEvent.

        Strips all outcome data (scores, winner, breakdown, earned RPs) to ensure
        clean temporal separation.

        Args:
            match: TBAMatch model instance or raw TBA match dictionary.
            event: Optional TBAEvent model instance or raw TBA event dictionary.

        Returns:
            Frozen MatchContext containing only pre-match information.
        """
        if isinstance(match, dict):
            m_key = str(match.get("key") or match.get("match_key", ""))
            ev_key = str(match.get("event_key", ""))
            comp_lvl = str(match.get("comp_level", "qm"))
            set_num = int(match.get("set_number", 1))
            match_num = int(match.get("match_number", 1))
            sched_time = match.get("time") or match.get("scheduled_time")
            act_time = match.get("actual_time")
            alliances = match.get("alliances", {})
            red_a = alliances.get("red", {}) if isinstance(alliances, dict) else {}
            blue_a = alliances.get("blue", {}) if isinstance(alliances, dict) else {}
            red_t = list(red_a.get("team_keys") or red_a.get("teams", []))
            blue_t = list(blue_a.get("team_keys") or blue_a.get("teams", []))
            red_s = list(
                red_a.get("surrogate_team_keys") or red_a.get("surrogates", [])
            )
            blue_s = list(
                blue_a.get("surrogate_team_keys") or blue_a.get("surrogates", [])
            )
        else:
            raw_k = (
                getattr(match, "key_name", None)
                or getattr(match, "match_key", None)
                or getattr(match, "key", "")
            )
            m_key = str(raw_k.id() if hasattr(raw_k, "id") else raw_k)
            raw_ek = (
                getattr(match, "event_key_name", None)
                or getattr(match, "event_key", None)
                or getattr(match, "event", "")
            )
            ev_key = str(raw_ek.id() if hasattr(raw_ek, "id") else raw_ek)
            comp_lvl = str(getattr(match, "comp_level", "qm"))
            set_num = int(getattr(match, "set_number", 1))
            match_num = int(getattr(match, "match_number", 1))
            sched_time = getattr(match, "time", None) or getattr(
                match, "scheduled_time", None
            )
            act_time = getattr(match, "actual_time", None)
            alliances = getattr(match, "alliances", {})
            red_a = alliances.get("red", {}) if isinstance(alliances, dict) else {}
            blue_a = alliances.get("blue", {}) if isinstance(alliances, dict) else {}
            red_t = list(red_a.get("team_keys") or red_a.get("teams", []))
            blue_t = list(blue_a.get("team_keys") or blue_a.get("teams", []))
            red_s = list(
                red_a.get("surrogate_team_keys") or red_a.get("surrogates", [])
            )
            blue_s = list(
                blue_a.get("surrogate_team_keys") or blue_a.get("surrogates", [])
            )

        # Normalize timestamps to unix int
        if hasattr(sched_time, "timestamp"):
            sched_time = int(sched_time.timestamp())
        elif sched_time is not None:
            sched_time = int(sched_time)

        if hasattr(act_time, "timestamp"):
            act_time = int(act_time.timestamp())
        elif act_time is not None:
            act_time = int(act_time)

        meta: Dict[str, Any] = {}
        if event is not None:
            if isinstance(event, dict):
                meta = dict(event)
            else:
                meta = {
                    "year": getattr(event, "year", None),
                    "week": getattr(event, "week", None),
                    "event_type": getattr(event, "event_type_enum", None)
                    or getattr(event, "event_type", None),
                    "name": getattr(event, "name", None),
                    "short_name": getattr(event, "short_name", None),
                }
        elif ev_key and len(ev_key) >= 4 and ev_key[:4].isdigit():
            meta = {"year": int(ev_key[:4])}

        return cls(
            match_key=m_key,
            event_key=ev_key,
            comp_level=comp_lvl,
            set_number=set_num,
            match_number=match_num,
            scheduled_time=sched_time,
            actual_time=act_time,
            red_teams=tuple(str(t) for t in red_t),
            blue_teams=tuple(str(t) for t in blue_t),
            event_metadata=_deep_freeze(meta),
            red_surrogates=tuple(str(t) for t in red_s),
            blue_surrogates=tuple(str(t) for t in blue_s),
        )

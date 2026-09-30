"""Post-match finalized outcome container.

Passed exclusively to BasePredictor.update during Phase 2 of chronological replay.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

from .adapter import _to_binary_int, extract_canonical_bonus_rps


@dataclass(frozen=True, init=False)
class MatchOutcome:
    """Finalized post-match result container.

    Encapsulates final scores, winning alliance, normalized win target,
    ranking points earned, and game-specific score breakdown.

    Attributes:
        match_key: Unique match identifier (e.g. '2024casj_qm1').
        red_score: Final score earned by Red alliance.
        blue_score: Final score earned by Blue alliance.
        event_key: Event identifier (e.g. '2024casj').
        winning_alliance: Winning alliance ('red', 'blue', or None for tie).
        actual_red_win: Normalized Red outcome: 1.0 (Red win), 0.0 (Blue win), 0.5 (Tie).
        red_rp_earned: Qualification ranking points earned by Red (None in playoffs).
        blue_rp_earned: Qualification ranking points earned by Blue (None in playoffs).
        red_teams: Roster of Red alliance team keys.
        blue_teams: Roster of Blue alliance team keys.
        score_breakdown: Game-specific detailed scoring breakdown dictionary.
        actual_time: Actual Unix timestamp when match began.
        comp_level: Tournament stage ('qm', 'ef', 'qf', 'sf', 'f').
        red_rp: Alias for red_rp_earned.
        blue_rp: Alias for blue_rp_earned.
        event_type: TBA event type of the event (pre-match metadata, the same value as
            `MatchContext.event_metadata["event_type"]`). None if unknown.
    """

    match_key: str
    red_score: int
    blue_score: int
    event_key: str = ""
    winning_alliance: Optional[str] = None
    actual_red_win: Optional[float] = None
    red_rp_earned: Optional[int] = None
    blue_rp_earned: Optional[int] = None
    red_teams: Tuple[str, ...] = ()
    blue_teams: Tuple[str, ...] = ()
    score_breakdown: Optional[Dict[str, Any]] = None
    actual_time: Optional[int] = None
    comp_level: Optional[str] = None
    red_rp: Optional[int] = None
    blue_rp: Optional[int] = None
    red_bonus_rps: Dict[str, int]
    blue_bonus_rps: Dict[str, int]
    red_surrogates: Tuple[str, ...] = ()
    blue_surrogates: Tuple[str, ...] = ()
    red_dqs: Tuple[str, ...] = ()
    blue_dqs: Tuple[str, ...] = ()
    event_type: Optional[int] = None

    def __init__(
        self,
        match_key: str,
        *args: Any,
        red_score: Optional[int] = None,
        blue_score: Optional[int] = None,
        event_key: str = "",
        winning_alliance: Optional[str] = None,
        actual_red_win: Optional[float] = None,
        red_rp_earned: Optional[int] = None,
        blue_rp_earned: Optional[int] = None,
        red_teams: Sequence[str] = (),
        blue_teams: Sequence[str] = (),
        score_breakdown: Optional[Dict[str, Any]] = None,
        actual_time: Optional[int] = None,
        comp_level: Optional[str] = None,
        red_rp: Optional[int] = None,
        blue_rp: Optional[int] = None,
        red_bonus_rps: Optional[Dict[str, int]] = None,
        blue_bonus_rps: Optional[Dict[str, int]] = None,
        win_target: Optional[float] = None,
        red_surrogates: Sequence[str] = (),
        blue_surrogates: Sequence[str] = (),
        red_dqs: Sequence[str] = (),
        blue_dqs: Sequence[str] = (),
        event_type: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MatchOutcome with robust support for positional and keyword arguments."""
        # Resolve positional arguments if passed
        if len(args) == 2 and red_score is None and blue_score is None:
            red_score = args[0]
            blue_score = args[1]
        elif len(args) >= 3:
            if not event_key:
                event_key = str(args[0])
            if red_score is None:
                red_score = args[1]
            if blue_score is None:
                blue_score = args[2]

        if red_score is None or blue_score is None:
            raise TypeError("MatchOutcome requires both red_score and blue_score.")

        # Validate scores
        if (
            isinstance(red_score, bool)
            or not isinstance(red_score, int)
            or red_score < 0
        ):
            raise ValueError(
                f"red_score must be a non-negative integer, got {red_score!r}"
            )
        if (
            isinstance(blue_score, bool)
            or not isinstance(blue_score, int)
            or blue_score < 0
        ):
            raise ValueError(
                f"blue_score must be a non-negative integer, got {blue_score!r}"
            )

        # Normalize winning alliance
        wa = winning_alliance
        if wa == "":
            wa = None
        if wa is not None and wa not in ("red", "blue"):
            raise ValueError(
                f"winning_alliance must be 'red', 'blue', or None; got {wa!r}"
            )

        # Deduce or validate actual_red_win
        actual_win = actual_red_win if actual_red_win is not None else win_target
        if actual_win is None:
            if wa == "red" or red_score > blue_score:
                actual_win = 1.0
            elif wa == "blue" or blue_score > red_score:
                actual_win = 0.0
            else:
                actual_win = 0.5
        else:
            if (
                isinstance(actual_win, bool)
                or not isinstance(actual_win, (int, float))
                or not math.isfinite(actual_win)
                or not (0.0 <= actual_win <= 1.0)
            ):
                raise ValueError(
                    f"actual_red_win must be a finite float in [0.0, 1.0], got {actual_win}"
                )
            actual_win = float(actual_win)

        # Reconcile ranking points
        if red_rp_earned is None and red_rp is not None:
            red_rp_earned = red_rp
        if blue_rp_earned is None and blue_rp is not None:
            blue_rp_earned = blue_rp
        if red_rp is None and red_rp_earned is not None:
            red_rp = red_rp_earned
        if blue_rp is None and blue_rp_earned is not None:
            blue_rp = blue_rp_earned

        # Validate ranking points
        if red_rp_earned is not None:
            if (
                isinstance(red_rp_earned, bool)
                or not isinstance(red_rp_earned, int)
                or red_rp_earned < 0
            ):
                raise ValueError(
                    f"red_rp_earned must be a non-negative integer, got {red_rp_earned!r}"
                )
        if blue_rp_earned is not None:
            if (
                isinstance(blue_rp_earned, bool)
                or not isinstance(blue_rp_earned, int)
                or blue_rp_earned < 0
            ):
                raise ValueError(
                    f"blue_rp_earned must be a non-negative integer, got {blue_rp_earned!r}"
                )

        object.__setattr__(self, "match_key", str(match_key))
        object.__setattr__(self, "red_score", int(red_score))
        object.__setattr__(self, "blue_score", int(blue_score))
        ek: Optional[str] = None
        if event_key is not None:
            ek_str = str(event_key).strip()
            if ek_str:
                ek = ek_str
        object.__setattr__(self, "event_key", ek)
        object.__setattr__(self, "winning_alliance", wa)
        object.__setattr__(self, "actual_red_win", actual_win)
        object.__setattr__(self, "red_rp_earned", red_rp_earned)
        object.__setattr__(self, "blue_rp_earned", blue_rp_earned)
        object.__setattr__(self, "red_rp", red_rp)
        object.__setattr__(self, "blue_rp", blue_rp)
        object.__setattr__(self, "red_teams", tuple(str(t) for t in red_teams))
        object.__setattr__(self, "blue_teams", tuple(str(t) for t in blue_teams))
        object.__setattr__(self, "score_breakdown", score_breakdown)
        object.__setattr__(
            self, "actual_time", int(actual_time) if actual_time is not None else None
        )
        cl: Optional[str] = None
        if comp_level is not None:
            cl_str = str(comp_level).strip().lower()
            if cl_str:
                cl = cl_str
        object.__setattr__(self, "comp_level", cl)
        object.__setattr__(
            self, "red_surrogates", tuple(str(t) for t in red_surrogates)
        )
        object.__setattr__(
            self, "blue_surrogates", tuple(str(t) for t in blue_surrogates)
        )
        object.__setattr__(self, "red_dqs", tuple(str(t) for t in red_dqs))
        object.__setattr__(self, "blue_dqs", tuple(str(t) for t in blue_dqs))
        if event_type is not None and (
            isinstance(event_type, bool) or not isinstance(event_type, int)
        ):
            raise ValueError(f"event_type must be an int or None, got {event_type!r}")
        object.__setattr__(self, "event_type", event_type)

        season = 0
        if "season" in kwargs:
            try:
                season = int(kwargs["season"])
            except (ValueError, TypeError):
                pass
        elif "year" in kwargs:
            try:
                season = int(kwargs["year"])
            except (ValueError, TypeError):
                pass
        if season == 0:
            for src in (ek, match_key):
                if src and len(str(src)) >= 4 and str(src)[:4].isdigit():
                    season = int(str(src)[:4])
                    break

        def _canonicalize_dict(
            d: Optional[Dict[str, Any]], alliance: str
        ) -> Dict[str, int]:
            if 0 < season < 2016:
                return {}
            allowed = (
                ("rp_1", "rp_2") if 0 < season < 2025 else ("rp_1", "rp_2", "rp_3")
            )
            if d is not None and any(k in allowed for k in d):
                return {k: _to_binary_int(v) for k, v in d.items() if k in allowed}
            if score_breakdown and isinstance(score_breakdown, dict) and season >= 2016:
                return extract_canonical_bonus_rps(
                    season, score_breakdown.get(alliance)
                )
            if d is not None:
                return {k: _to_binary_int(v) for k, v in d.items() if k in allowed}
            return {}

        r_bonuses = _canonicalize_dict(red_bonus_rps, "red")
        b_bonuses = _canonicalize_dict(blue_bonus_rps, "blue")

        object.__setattr__(self, "red_bonus_rps", r_bonuses)
        object.__setattr__(self, "blue_bonus_rps", b_bonuses)

    @property
    def is_tie(self) -> bool:
        """Return True if the win label is a tie (0.5)."""
        return self.actual_red_win == 0.5

    @property
    def win_target(self) -> float:
        """Target outcome value: 1.0 for Red win, 0.0 for Blue win, 0.5 for Tie."""
        assert self.actual_red_win is not None
        return self.actual_red_win

    @property
    def actual_blue_win(self) -> float:
        """Target outcome value for Blue alliance: 1.0 - actual_red_win."""
        assert self.actual_red_win is not None
        return 1.0 - self.actual_red_win

    @classmethod
    def from_tba_match(
        cls,
        match: Any,
        tie_policy: Optional[str] = None,
        event_type: Optional[int] = None,
    ) -> MatchOutcome:
        """Construct a MatchOutcome from a TBAMatch instance or raw TBA dictionary.

        Raises ValueError if the match has not been completed (score == -1).
        Nullifies ranking points for playoff matches (comp_level != 'qm').

        Args:
            match: TBAMatch or raw TBA match dictionary.
            tie_policy: Win label policy ('advancer' or 'score'). See config.TIE_POLICIES.
            event_type: TBA event type from the event metadata (optional).
        """
        if isinstance(match, dict):
            m_key = str(match.get("key") or match.get("match_key", ""))
            ev_key = str(match.get("event_key", ""))
            comp_lvl = str(match.get("comp_level", "qm"))
            act_time = match.get("actual_time")
            alliances = match.get("alliances", {})
            red_a = alliances.get("red", {}) if isinstance(alliances, dict) else {}
            blue_a = alliances.get("blue", {}) if isinstance(alliances, dict) else {}
            red_s = int(red_a.get("score", -1))
            blue_s = int(blue_a.get("score", -1))
            red_t = list(red_a.get("team_keys") or red_a.get("teams", []))
            blue_t = list(blue_a.get("team_keys") or blue_a.get("teams", []))
            red_surr = list(
                red_a.get("surrogate_team_keys") or red_a.get("surrogates", [])
            )
            blue_surr = list(
                blue_a.get("surrogate_team_keys") or blue_a.get("surrogates", [])
            )
            red_dq = list(red_a.get("dq_team_keys") or red_a.get("dqs", []))
            blue_dq = list(blue_a.get("dq_team_keys") or blue_a.get("dqs", []))
            wa = match.get("winning_alliance")
            score_bd = match.get("score_breakdown")
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
            act_time = getattr(match, "actual_time", None)
            alliances = getattr(match, "alliances", {})
            red_a = alliances.get("red", {}) if isinstance(alliances, dict) else {}
            blue_a = alliances.get("blue", {}) if isinstance(alliances, dict) else {}
            red_s = int(red_a.get("score", -1))
            blue_s = int(blue_a.get("score", -1))
            red_t = list(red_a.get("team_keys") or red_a.get("teams", []))
            blue_t = list(blue_a.get("team_keys") or blue_a.get("teams", []))
            red_surr = list(
                red_a.get("surrogate_team_keys") or red_a.get("surrogates", [])
            )
            blue_surr = list(
                blue_a.get("surrogate_team_keys") or blue_a.get("surrogates", [])
            )
            red_dq = list(red_a.get("dq_team_keys") or red_a.get("dqs", []))
            blue_dq = list(blue_a.get("dq_team_keys") or blue_a.get("dqs", []))
            wa = getattr(match, "winning_alliance", None)
            score_bd = getattr(match, "score_breakdown", None)

        if hasattr(act_time, "timestamp"):
            act_time = int(act_time.timestamp())
        elif act_time is not None:
            act_time = int(act_time)

        if red_s < 0 or blue_s < 0:
            raise ValueError(
                f"Cannot construct MatchOutcome from unplayed match '{m_key}'"
            )

        if wa not in ("red", "blue"):
            if red_s > blue_s:
                wa = "red"
            elif blue_s > red_s:
                wa = "blue"
            else:
                wa = None

        actual_win = 1.0 if wa == "red" else (0.0 if wa == "blue" else 0.5)

        # Extract RPs
        red_rp = None
        blue_rp = None
        if score_bd and isinstance(score_bd, dict) and comp_lvl == "qm":
            red_rp = score_bd.get("red", {}).get("rp") or score_bd.get("red", {}).get(
                "rankingPoints"
            )
            blue_rp = score_bd.get("blue", {}).get("rp") or score_bd.get(
                "blue", {}
            ).get("rankingPoints")

        season = (
            int(ev_key[:4])
            if ev_key and len(ev_key) >= 4 and ev_key[:4].isdigit()
            else 0
        )
        red_bonus = extract_canonical_bonus_rps(
            season, score_bd.get("red") if score_bd else None
        )
        blue_bonus = extract_canonical_bonus_rps(
            season, score_bd.get("blue") if score_bd else None
        )

        return cls(
            match_key=m_key,
            event_key=ev_key,
            red_score=red_s,
            blue_score=blue_s,
            winning_alliance=wa,
            actual_red_win=actual_win,
            red_rp_earned=red_rp,
            blue_rp_earned=blue_rp,
            red_rp=red_rp,
            blue_rp=blue_rp,
            red_teams=tuple(str(t) for t in red_t),
            blue_teams=tuple(str(t) for t in blue_t),
            score_breakdown=score_bd,
            actual_time=act_time,
            comp_level=comp_lvl,
            red_bonus_rps=red_bonus,
            blue_bonus_rps=blue_bonus,
            red_surrogates=tuple(str(t) for t in red_surr),
            blue_surrogates=tuple(str(t) for t in blue_surr),
            red_dqs=tuple(str(t) for t in red_dq),
            blue_dqs=tuple(str(t) for t in blue_dq),
            event_type=event_type,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert container to a JSON-serializable dictionary."""
        return {
            "match_key": self.match_key,
            "event_key": self.event_key,
            "red_score": self.red_score,
            "blue_score": self.blue_score,
            "winning_alliance": self.winning_alliance,
            "actual_red_win": self.actual_red_win,
            "red_rp_earned": self.red_rp_earned,
            "blue_rp_earned": self.blue_rp_earned,
            "red_bonus_rps": dict(self.red_bonus_rps),
            "blue_bonus_rps": dict(self.blue_bonus_rps),
            "red_teams": list(self.red_teams),
            "blue_teams": list(self.blue_teams),
            "red_surrogates": list(self.red_surrogates),
            "blue_surrogates": list(self.blue_surrogates),
            "red_dqs": list(self.red_dqs),
            "blue_dqs": list(self.blue_dqs),
            "is_tie": self.is_tie,
            "actual_time": self.actual_time,
            "comp_level": self.comp_level,
        }

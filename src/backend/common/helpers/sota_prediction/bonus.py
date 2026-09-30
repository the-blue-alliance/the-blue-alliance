"""Rulebook bonus ranking point model.

Each bonus RP is a rulebook rule on quantities that the TBA breakdown records:
a threshold on a game-piece count, a threshold on endgame points, or a
conjunction of such conditions. The thresholds depend on the event type
(regional or district event, district championship, championship). See
`docs/rp_threshold_audit.md` for the audit of every threshold against the TBA
flags.

The model has three layers.

1. Team channels. Each season defines the quantities that its rules use. Three
   channel types learn team-level abilities online, and reset every season:

   * ``SumChannel``: an alliance count that is the sum of team contributions
     (for example 2024 notes or 2023 links). Each team has a Gaussian state.
     The alliance value is Normal(sum of means, sum of variances + noise).
   * ``RobotChannel``: a per-robot state that the breakdown records per
     driver station (for example 2022 hangar rung or 2025 cage). Each team has
     a categorical distribution (decayed counts shrunk to the season mix). The
     alliance total is the exact convolution over the three robots.
   * ``BinChannel``: an alliance-level yes/no event that depends on the teams
     (for example the 2024 coopertition button or the 2018 levitate). Each team
     has a shrunk rate. The alliance rate is the mean of the team rates.

2. Rule probability. The season rule combines channel distributions with the
   event-type threshold, for example P(notes >= 18) at a regional, with the
   coopertition mixture where the rule has one.

3. Calibration and awards. An online logistic model maps logit(p_rule) to the
   probability that the rule is met. The target is the rule outcome computed
   from the breakdown. The TBA flag can also be set by a foul award or an
   exemption (for example G424 in 2024 awards the Ensemble RP). A per-key rate
   of flags among rule-not-met rows learns this online. A second per-key rate
   learns flags that are absent although the rule is met. The final probability
   is p_met * (1 - deny_rate) + (1 - p_met) * award_rate.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .rp import OnlineLogit

# ---------------------------------------------------------------- event tiers
# Championship event codes (event key without the year), 2016-2025. Measured
# against TBA event_type on every cached in-season match: 100% agreement.
_CMP_CODES = frozenset(
    {
        "arc",
        "cars",
        "carv",
        "cur",
        "dal",
        "dar",
        "gal",
        "hop",
        "joh",
        "mil",
        "new",
        "roe",
        "tes",
        "tur",
        "cmp",
        "cmptx",
        "cmpmo",
        "cmpmi",
        "cc",
    }
)


def tier_of(event_key: str, event_type: Optional[int] = None) -> str:
    """Return 'reg', 'dcmp' or 'cmp'. TBA event_type is authoritative when given."""
    if event_type in (3, 4):
        return "cmp"
    if event_type in (2, 5):
        return "dcmp"
    if event_type in (0, 1):
        return "reg"
    code = (event_key or "")[4:].lower()
    if code in _CMP_CODES:
        return "cmp"
    if "cmp" in code:
        return "dcmp"
    return "reg"


# Rulebook thresholds by tier. Values audited in docs/rp_threshold_audit.md.
TIER_THRESHOLDS: Dict[int, Dict[str, Dict[str, Any]]] = {
    2016: {t: {"tower": 10 if t == "cmp" else 8} for t in ("reg", "dcmp", "cmp")},
    2023: {"reg": {"links": 5}, "dcmp": {"links": 5}, "cmp": {"links": 6}},
    2024: {
        "reg": {"notes": 18, "notes_coop": 15},
        "dcmp": {"notes": 21, "notes_coop": 18},
        "cmp": {"notes": 25, "notes_coop": 21},
    },
    2025: {
        "reg": {"coral": 5, "barge": 14},
        "dcmp": {"coral": 5, "barge": 14},
        "cmp": {"coral": 7, "barge": 16},
    },
    # 2026 REBUILT, Game Manual TU22 Table 6-5 (from the manual, not audited against data).
    2026: {
        "reg": {"energized": 100, "supercharged": 360, "traversal": 50},
        "dcmp": {"energized": 240, "supercharged": 360, "traversal": 50},
        "cmp": {"energized": 360, "supercharged": 500, "traversal": 50},
    },
}

SUPPORTED_BONUS_SEASONS = frozenset(
    {2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024, 2025, 2026}
)


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _logit(p: float) -> float:
    p = min(max(p, 1e-4), 1.0 - 1e-4)
    return math.log(p / (1.0 - p))


def _tail_normal(mean: float, var: float, t: float) -> float:
    """P(X >= t) for an integer count X approximated by Normal(mean, var)."""
    return 1.0 - _phi((t - 0.5 - mean) / math.sqrt(max(var, 1e-6)))


def _poibin_tail(ps: Sequence[float], k: int) -> float:
    """P(sum of independent Bernoulli(ps) >= k)."""
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for i, d in enumerate(dist):
            nxt[i] += d * (1.0 - p)
            nxt[i + 1] += d * p
        dist = nxt
    return float(sum(dist[k:])) if k < len(dist) else 0.0


def _convolve(dists: Sequence[Dict[Any, float]], add) -> Dict[Any, float]:
    out: Dict[Any, float] = {None: 1.0}
    for d in dists:
        nxt: Dict[Any, float] = {}
        for a, pa in out.items():
            for b, pb in d.items():
                v = b if a is None else add(a, b)
                nxt[v] = nxt.get(v, 0.0) + pa * pb
        out = nxt
    return out


# ------------------------------------------------------------------ channels
class SumChannel:
    """Alliance count = sum of team contributions + noise (Gaussian, online)."""

    def __init__(self, q_frac: float, prior_share: float, z_prior: float = 0.0) -> None:
        self.q_frac = q_frac
        self.prior_share = prior_share
        self.z_prior = float(z_prior)
        self.teams: Dict[str, Tuple[float, float]] = {}
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.r_sum = 0.0
        self.r_n = 0

    def _alliance_var(self) -> float:
        if self.n < 2:
            return 1.0
        return max(self.m2 / (self.n - 1), 1e-3)

    def _prior(self, n_teams: int) -> Tuple[float, float]:
        v = self._alliance_var()
        return self.mean / max(n_teams, 1), self.prior_share * v / max(n_teams, 1)

    def _team_state(
        self, t: str, m0: float, p0: float, z_map: Optional[Mapping[str, float]] = None
    ) -> Tuple[float, float]:
        st = self.teams.get(t)
        if st is not None:
            return st
        if self.z_prior > 0.0 and z_map is not None and t in z_map:
            zt = float(z_map[t])
            return (
                m0 + self.z_prior * zt * math.sqrt(max(p0, 1e-6)),
                p0 * max(1.0 - 0.5 * self.z_prior * self.z_prior, 0.25),
            )
        return m0, p0

    def _noise(self) -> float:
        v = self._alliance_var()
        base = (1.0 - self.prior_share) * v
        if self.r_n == 0:
            return base
        w = self.r_n / (self.r_n + 20.0)
        return max((1 - w) * base + w * self.r_sum / self.r_n, 1e-3)

    def ready(self) -> bool:
        return self.n >= 2

    def predict(
        self, teams: Sequence[str], z_map: Optional[Mapping[str, float]] = None
    ) -> Tuple[float, float]:
        m0, p0 = self._prior(len(teams))
        mean = 0.0
        var = 0.0
        for t in teams:
            m, p = self._team_state(t, m0, p0, z_map)
            mean += m
            var += p
        return mean, var + self._noise()

    def update(
        self,
        teams: Sequence[str],
        y: float,
        z_map: Optional[Mapping[str, float]] = None,
    ) -> None:
        if self.ready():
            m0, p0 = self._prior(len(teams))
            q = self.q_frac * p0
            st = [self._team_state(t, m0, p0, z_map) for t in teams]
            st = [(m, p + q) for m, p in st]
            r = self._noise()
            s = sum(p for _, p in st) + r
            e = y - sum(m for m, _ in st)
            for t, (m, p) in zip(teams, st):
                k = p / s
                self.teams[t] = (m + k * e, max(p - k * p, 1e-6))
            self.r_sum += max(e * e - (s - r), 0.0)
            self.r_n += 1
        self.n += 1
        d = y - self.mean
        self.mean += d / self.n
        self.m2 += d * (y - self.mean)


class RobotChannel:
    """Per-robot categorical state with decayed team counts shrunk to the season mix."""

    def __init__(self, n_states: int, decay: float, prior_n: float) -> None:
        self.k = n_states
        self.decay = decay
        self.prior_n = prior_n
        self.teams: Dict[str, np.ndarray] = {}
        self.season = np.ones(n_states)

    def probs(self, team: str) -> np.ndarray:
        f = self.season / self.season.sum()
        c = self.teams.get(team)
        if c is None:
            return f
        return (c + self.prior_n * f) / (c.sum() + self.prior_n)

    def update(self, team: str, state: int) -> None:
        c = self.teams.get(team)
        if c is None:
            c = np.zeros(self.k)
        c = c * self.decay
        c[state] += 1.0
        self.teams[team] = c
        self.season[state] += 1.0


class BinChannel:
    """Alliance-level binary event with shrunk team rates."""

    def __init__(self, decay: float, prior_n: float) -> None:
        self.decay = decay
        self.prior_n = prior_n
        self.teams: Dict[str, Tuple[float, float]] = {}
        self.a = 1.0
        self.b = 1.0

    def prob(self, teams: Sequence[str]) -> float:
        r = self.a / (self.a + self.b)
        ps = []
        for t in teams:
            a, b = self.teams.get(t, (0.0, 0.0))
            ps.append((a + self.prior_n * r) / (a + b + self.prior_n))
        return float(np.mean(ps)) if ps else r

    def update(self, teams: Sequence[str], y: int) -> None:
        for t in teams:
            a, b = self.teams.get(t, (0.0, 0.0))
            self.teams[t] = (a * self.decay + y, b * self.decay + (1 - y))
        self.a += y
        self.b += 1 - y


# --------------------------------------------------------- season rulebooks
def _reef_levels(bd: Mapping[str, Any]) -> List[int]:
    """2025 coral scored per level [L1, L2, L3, L4] for the Coral RP rule.

    TBA semantics (checked on every 2025 breakdown in the stream, labels only):

    - ``trough`` is a per-period count. ``teleopReef.trough`` holds only the coral scored in
      teleop: 2 * teleop trough + branch points reproduces ``teleopCoralPoints`` for 100% of
      alliances, and a cumulative trough fails for 32%. L1 is therefore auto + teleop trough.
    - The branch grids (``botRow``/``midRow``/``topRow``) hold node states. ``teleopReef`` is
      the end-of-match state, so it misses auto coral that was later removed. FMS scores each
      node once: auto points for the auto nodes, teleop points for the other end-state nodes.
      L2-L4 are therefore the union of the auto and teleop nodes. This union reproduces the TBA
      Coral RP flag for 29,609 of 29,610 qualification alliances (end state only: 29,605).
    """
    tr = bd.get("teleopReef") or {}
    ar = bd.get("autoReef") or {}

    def cnt(row: str) -> int:
        nodes = {k for k, v in (tr.get(row) or {}).items() if v}
        nodes |= {k for k, v in (ar.get(row) or {}).items() if v}
        return len(nodes)

    return [
        int((tr.get("trough") or 0) + (ar.get("trough") or 0)),
        cnt("botRow"),
        cnt("midRow"),
        cnt("topRow"),
    ]


def _rocket_max(bd: Mapping[str, Any]) -> int:
    val = {"Panel": 1, "PanelAndCargo": 2, "Cargo": 1}
    best = 0
    for side in ("Near", "Far"):
        tot = 0
        for lvl in ("low", "mid", "top"):
            for lr in ("Left", "Right"):
                tot += val.get(str(bd.get(f"{lvl}{lr}Rocket{side}")), 0)
        best = max(best, tot)
    return best


def _charge_2023(bd: Mapping[str, Any], n: int) -> Optional[int]:
    a = bd.get(f"autoChargeStationRobot{n}")
    e = bd.get(f"endGameChargeStationRobot{n}")
    if a is None or e is None:
        return None
    pts = 0
    if a == "Docked":
        pts += 12 if bd.get("autoBridgeState") == "Level" else 8
    if e == "Docked":
        pts += 10 if bd.get("endGameBridgeState") == "Level" else 6
    return pts


# 2026 TOWER, Game Manual TU22 Table 6-4. AUTO: 15 points per robot at LEVEL 1, 2 robots
# max. TELEOP: 10 / 20 / 30 points for LEVEL 1 / 2 / 3, one LEVEL per robot. A robot can
# earn AUTO and TELEOP TOWER points in the same match.
_TOWER_TELEOP_2026 = {"Level1": 1, "Level2": 2, "Level3": 3}
_TOWER_TELEOP_PTS_2026 = (0, 10, 20, 30)
_TOWER_AUTO_PTS_2026 = 15
_TOWER_AUTO_MAX_2026 = 2


def _tower_state_2026(bd: Mapping[str, Any], n: int) -> Optional[int]:
    """Joint robot state 4 * auto + teleop: auto in {0, 1} (LEVEL 1), teleop in {0..3}."""
    a = bd.get(f"autoTowerRobot{n}")
    e = bd.get(f"endGameTowerRobot{n}")
    if a is None or e is None:
        return None
    return 4 * int(a == "Level1") + _TOWER_TELEOP_2026.get(str(e), 0)


def _fuel_2026(bd: Mapping[str, Any]) -> float:
    """FUEL scored in an active HUB.

    Each active-HUB FUEL is worth 1 point in AUTO and TELEOP, and inactive-HUB FUEL is
    worth 0 (Table 6-4), so ``hubScore.totalPoints`` equals the active-HUB FUEL count.
    ``totalCount`` may also include inactive-HUB FUEL, so it is not used.
    """
    hub = bd.get("hubScore") or {}
    return float(hub.get("totalPoints") or 0)


# Robot channel definitions: name -> (field template, {value: state index}, state points).
_ROBOT_DEFS: Dict[int, Dict[str, Tuple[str, Dict[str, int], Tuple[int, ...]]]] = {
    2018: {
        "autorun": ("autoRobot{n}", {"AutoRun": 1}, (0, 1)),
        "climb": ("endgameRobot{n}", {"Climbing": 1}, (0, 1)),
    },
    2019: {
        "hab": (
            "endgameRobot{n}",
            {"HabLevel1": 1, "HabLevel2": 2, "HabLevel3": 3},
            (0, 3, 6, 12),
        )
    },
    2020: {"eg": ("endgameRobot{n}", {"Park": 1, "Hang": 2}, (0, 5, 25))},
    2022: {
        "hang": (
            "endgameRobot{n}",
            {"Low": 1, "Mid": 2, "High": 3, "Traversal": 4},
            (0, 4, 6, 10, 15),
        )
    },
    2023: {"charge": ("", {}, (0, 6, 8, 10, 12, 14, 16, 18, 20, 22))},
    2024: {
        "stage": (
            "endGameRobot{n}",
            {"Parked": 1, "StageLeft": 2, "StageRight": 2, "CenterStage": 2},
            (0, 1, 3),
        )
    },
    2025: {
        "leave": ("autoLineRobot{n}", {"Yes": 1}, (0, 1)),
        "barge": (
            "endGameRobot{n}",
            {"Parked": 1, "ShallowCage": 2, "DeepCage": 3},
            (0, 2, 6, 12),
        ),
    },
    # Joint AUTO/TELEOP tower state (see _tower_state_2026). The points ignore the AUTO cap.
    # _traversal_2026 applies the cap.
    2026: {
        "tower": (
            "",
            {},
            tuple(
                _TOWER_AUTO_PTS_2026 * a + _TOWER_TELEOP_PTS_2026[e]
                for a in (0, 1)
                for e in range(4)
            ),
        ),
    },
}
_CHARGE_STATES = {v: i for i, v in enumerate(_ROBOT_DEFS[2023]["charge"][2])}

_SUM_DEFS: Dict[int, Tuple[str, ...]] = {
    2016: ("damaged", "boulders", "faces"),
    2017: ("kpa", "rotors"),
    2019: ("rocket",),
    2020: ("cells",),
    2022: ("cargo", "acargo"),
    2023: ("links", "coopgp"),
    2024: ("notes",),
    2025: ("acoral", "L1", "L2", "L3", "L4"),
    2026: ("fuel",),
}

_BIN_DEFS: Dict[int, Tuple[str, ...]] = {
    2018: ("switch0", "lev"),
    2020: ("level",),
    2024: ("coop",),
    2025: ("coop",),
}


def _sum_obs(season: int, bd: Mapping[str, Any]) -> Dict[str, float]:
    g = bd.get
    if season == 2016:
        return {
            "damaged": sum(
                1 for i in range(1, 6) if (g(f"position{i}crossings") or 0) >= 2
            ),
            "boulders": sum(
                g(k) or 0
                for k in (
                    "autoBouldersHigh",
                    "autoBouldersLow",
                    "teleopBouldersHigh",
                    "teleopBouldersLow",
                )
            ),
            "faces": sum(
                1
                for k in ("towerFaceA", "towerFaceB", "towerFaceC")
                if g(k) in ("Challenged", "Scaled")
            ),
        }
    if season == 2017:
        return {
            "kpa": (g("autoFuelPoints") or 0) + (g("teleopFuelPoints") or 0),
            "rotors": sum(1 for i in range(1, 5) if g(f"rotor{i}Engaged")),
        }
    if season == 2019:
        return {"rocket": _rocket_max(bd)}
    if season == 2020:
        return {
            "cells": sum(
                g(f"{p}Cells{w}") or 0
                for p in ("auto", "teleop")
                for w in ("Bottom", "Outer", "Inner")
            )
        }
    if season == 2022:
        return {"cargo": g("matchCargoTotal") or 0, "acargo": g("autoCargoTotal") or 0}
    if season == 2023:
        return {
            "links": (g("linkPoints") or 0) // 5,
            "coopgp": g("coopGamePieceCount") or 0,
        }
    if season == 2024:
        return {
            "notes": sum(
                g(k) or 0
                for k in (
                    "autoAmpNoteCount",
                    "autoSpeakerNoteCount",
                    "teleopAmpNoteCount",
                    "teleopSpeakerNoteCount",
                    "teleopSpeakerNoteAmplifiedCount",
                )
            )
        }
    if season == 2025:
        lv = _reef_levels(bd)
        out = {"acoral": g("autoCoralCount") or 0}
        out.update({f"L{i + 1}": lv[i] for i in range(4)})
        return out
    if season == 2026:
        return {"fuel": _fuel_2026(bd)}
    return {}


def _robot_obs(
    season: int, bd: Mapping[str, Any], n_robots: int
) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for name, (tmpl, table, _) in _ROBOT_DEFS.get(season, {}).items():
        states: List[int] = []
        for n in range(1, n_robots + 1):
            if season == 2023:
                pts = _charge_2023(bd, n)
                if pts is None:
                    states = []
                    break
                states.append(_CHARGE_STATES.get(pts, 0))
            elif season == 2026:
                st = _tower_state_2026(bd, n)
                if st is None:
                    states = []
                    break
                states.append(st)
            else:
                v = bd.get(tmpl.format(n=n))
                if v is None:
                    states = []
                    break
                states.append(table.get(str(v), 0))
        if states:
            out[name] = states
    return out


def _bin_obs(
    season: int, bd: Mapping[str, Any], robot: Dict[str, List[int]]
) -> Dict[str, int]:
    g = bd.get
    if season == 2018:
        return {
            "switch0": int(bool(g("autoSwitchAtZero"))),
            "lev": int((g("vaultLevitatePlayed") or 0) >= 3),
        }
    if season == 2020:
        hangs = sum(1 for s in robot.get("eg", []) if s == 2)
        if hangs == 0:
            return {}
        return {"level": int(g("endgameRungIsLevel") == "IsLevel")}
    if season == 2024:
        return {"coop": int(bool(g("coopNotePlayed")))}
    if season == 2025:
        return {"coop": int(bool(g("coopertitionCriteriaMet")))}
    return {}


def rule_met(
    season: int, tier: str, bd: Mapping[str, Any], obd: Mapping[str, Any]
) -> Dict[str, int]:
    """Rule outcome computed from the breakdown (flag without awards)."""
    g = bd.get
    thr = TIER_THRESHOLDS.get(season, {}).get(tier, {})
    if season == 2016:
        s = _sum_obs(season, bd)
        return {
            "rp_1": int(s["damaged"] >= 4),
            "rp_2": int(s["boulders"] >= thr["tower"] and s["faces"] >= 3),
        }
    if season == 2017:
        s = _sum_obs(season, bd)
        return {"rp_1": int(s["kpa"] >= 40), "rp_2": int(s["rotors"] >= 4)}
    if season == 2018:
        runs = sum(1 for i in range(1, 4) if g(f"autoRobot{i}") == "AutoRun")
        climbs = sum(1 for i in range(1, 4) if g(f"endgameRobot{i}") == "Climbing")
        lev = int((g("vaultLevitatePlayed") or 0) >= 3)
        return {
            "rp_1": int(runs >= 3 and bool(g("autoSwitchAtZero"))),
            "rp_2": int(climbs + lev >= 3),
        }
    if season == 2019:
        return {
            "rp_1": int(
                bool(g("completedRocketNear")) or bool(g("completedRocketFar"))
            ),
            "rp_2": int((g("habClimbPoints") or 0) >= 15),
        }
    if season == 2020:
        return {
            "rp_1": int((g("endgamePoints") or 0) >= 65),
            "rp_2": int(bool(g("stage3Activated"))),
        }
    if season == 2022:
        cargo = g("matchCargoTotal") or 0
        q = bool(g("quintetAchieved"))
        return {
            "rp_1": int(cargo >= 20 or (q and cargo >= 18)),
            "rp_2": int((g("endgamePoints") or 0) >= 16),
        }
    if season == 2023:
        coop = bool(g("coopertitionCriteriaMet")) and bool(
            obd.get("coopertitionCriteriaMet")
        )
        n = thr["links"] - (1 if coop else 0)
        return {
            "rp_1": int((g("linkPoints") or 0) // 5 >= n),
            "rp_2": int((g("totalChargeStationPoints") or 0) >= 26),
        }
    if season == 2024:
        s = _sum_obs(season, bd)
        coop = bool(g("coopertitionBonusAchieved"))
        need = thr["notes_coop"] if coop else thr["notes"]
        onstage = sum(
            1
            for i in range(1, 4)
            if g(f"endGameRobot{i}") in ("StageLeft", "StageRight", "CenterStage")
        )
        return {
            "rp_1": int(s["notes"] >= need),
            "rp_2": int((g("endGameTotalStagePoints") or 0) >= 10 and onstage >= 2),
        }
    if season == 2025:
        leave = all(g(f"autoLineRobot{i}") == "Yes" for i in range(1, 4))
        lv = _reef_levels(bd)
        coop = bool(g("coopertitionCriteriaMet")) and bool(
            obd.get("coopertitionCriteriaMet")
        )
        need_levels = 3 if coop else 4
        return {
            "rp_1": int(leave and (g("autoCoralCount") or 0) >= 1),
            "rp_2": int(sum(1 for c in lv if c >= thr["coral"]) >= need_levels),
            "rp_3": int((g("endGameBargePoints") or 0) >= thr["barge"]),
        }
    if season == 2026:
        fuel = _fuel_2026(bd)
        return {
            "rp_1": int(fuel >= thr["energized"]),
            "rp_2": int(fuel >= thr["supercharged"]),
            "rp_3": int((g("totalTowerPoints") or 0) >= thr["traversal"]),
        }
    return {}


# ------------------------------------------------------------------- model
class RuleBonusModel:
    """Per-season rulebook bonus RP model (see module docstring)."""

    def __init__(self, params: Mapping[str, Any]) -> None:
        self.p = dict(params)
        self.season: Optional[int] = None
        self.reset_season(None)

    # ---- lifecycle
    def reset_season(self, season: Optional[int]) -> None:
        self.season = season
        p = self.p
        zp = float(p.get("rb_z_prior", 0.0))
        self.sums: Dict[str, SumChannel] = {
            k: SumChannel(p["rb_q_frac"], p["rb_prior_share"], zp)
            for k in _SUM_DEFS.get(season or 0, ())
        }
        self.robots: Dict[str, RobotChannel] = {
            k: RobotChannel(len(v[2]), p["rb_decay"], p["rb_prior_n"])
            for k, v in _ROBOT_DEFS.get(season or 0, {}).items()
        }
        self.bins: Dict[str, BinChannel] = {
            k: BinChannel(p["rb_decay"], p["rb_prior_n"])
            for k in _BIN_DEFS.get(season or 0, ())
        }
        # 2024 Ensemble: stage bonus points (spotlight, harmony, trap) given k robots onstage.
        self.extra24 = [{} for _ in range(4)]
        # Direct team propensity for each bonus flag (alliance flag = sum of team parts).
        self.flags: Dict[str, SumChannel] = {}
        self.cal: Dict[str, OnlineLogit] = {}
        self.award: Dict[str, List[float]] = {}
        self.deny: Dict[str, List[float]] = {}

    def supported(self) -> bool:
        return self.season in SUPPORTED_BONUS_SEASONS

    # ---- channel helpers
    def _sum_tail(
        self,
        name: str,
        teams: Sequence[str],
        t: float,
        z_map: Optional[Mapping[str, float]] = None,
    ) -> Optional[float]:
        ch = self.sums[name]
        if not ch.ready():
            return None
        m, v = ch.predict(teams, z_map)
        return _tail_normal(m, v, t)

    def _robot_dist(self, name: str, teams: Sequence[str]) -> Dict[int, float]:
        ch = self.robots[name]
        pts = _ROBOT_DEFS[self.season][name][2]
        dists = []
        for t in teams:
            pr = ch.probs(t)
            d: Dict[int, float] = {}
            for i, pi in enumerate(pr):
                d[pts[i]] = d.get(pts[i], 0.0) + float(pi)
            dists.append(d)
        return _convolve(dists, lambda a, b: a + b)

    def _robot_state_probs(
        self, name: str, teams: Sequence[str], state: int
    ) -> List[float]:
        ch = self.robots[name]
        return [float(ch.probs(t)[state]) for t in teams]

    @staticmethod
    def _tail(dist: Mapping[int, float], t: float) -> float:
        return float(sum(p for v, p in dist.items() if v >= t))

    # ---- rule probabilities
    def rule_probs(
        self,
        tier: str,
        teams: Sequence[str],
        opp: Sequence[str],
        z_map: Optional[Mapping[str, float]] = None,
    ) -> Dict[str, Optional[float]]:
        y = self.season
        if not self.p["rb_tier"]:
            tier = "reg"
        thr = TIER_THRESHOLDS.get(y, {}).get(tier, {})
        out: Dict[str, Optional[float]] = {}
        if y == 2016:
            out["rp_1"] = self._sum_tail("damaged", teams, 4, z_map)
            a = self._sum_tail("boulders", teams, thr["tower"], z_map)
            b = self._sum_tail("faces", teams, 3, z_map)
            out["rp_2"] = None if a is None or b is None else a * b
        elif y == 2017:
            out["rp_1"] = self._sum_tail("kpa", teams, 40, z_map)
            out["rp_2"] = self._sum_tail("rotors", teams, 4, z_map)
        elif y == 2018:
            runs = self._robot_state_probs("autorun", teams, 1)
            out["rp_1"] = float(np.prod(runs)) * self.bins["switch0"].prob(teams)
            climbs = self._robot_state_probs("climb", teams, 1)
            out["rp_2"] = _poibin_tail(climbs + [self.bins["lev"].prob(teams)], 3)
        elif y == 2019:
            out["rp_1"] = self._sum_tail("rocket", teams, 12, z_map)
            out["rp_2"] = self._tail(self._robot_dist("hab", teams), 15)
        elif y == 2020:
            d = self._robot_dist("eg", teams)
            lvl = self.bins["level"].prob(teams)
            out["rp_1"] = self._tail(d, 65) + lvl * float(
                sum(p for v, p in d.items() if 50 <= v < 65)
            )
            out["rp_2"] = self._sum_tail("cells", teams, 49, z_map)
        elif y == 2022:
            q = self._sum_tail("acargo", teams, 5, z_map)
            a18 = self._sum_tail("cargo", teams, 18, z_map)
            a20 = self._sum_tail("cargo", teams, 20, z_map)
            out["rp_1"] = None if q is None or a18 is None else q * a18 + (1 - q) * a20
            out["rp_2"] = self._tail(self._robot_dist("hang", teams), 16)
        elif y == 2023:
            c_own = self._sum_tail("coopgp", teams, 3, z_map)
            c_opp = self._sum_tail("coopgp", opp, 3, z_map)
            n = thr["links"]
            lo = self._sum_tail("links", teams, n - 1, z_map)
            hi = self._sum_tail("links", teams, n, z_map)
            if None in (c_own, c_opp, lo, hi):
                out["rp_1"] = None
            else:
                c = c_own * c_opp
                out["rp_1"] = c * lo + (1 - c) * hi
            out["rp_2"] = self._tail(self._robot_dist("charge", teams), 26)
        elif y == 2024:
            c = self.bins["coop"].prob(teams) * self.bins["coop"].prob(opp)
            lo = self._sum_tail("notes", teams, thr["notes_coop"], z_map)
            hi = self._sum_tail("notes", teams, thr["notes"], z_map)
            out["rp_1"] = None if lo is None else c * lo + (1 - c) * hi
            out["rp_2"] = self._ensemble_2024(teams)
        elif y == 2025:
            leave = self._robot_state_probs("leave", teams, 1)
            ac = self._sum_tail("acoral", teams, 1, z_map)
            out["rp_1"] = None if ac is None else float(np.prod(leave)) * ac
            lv = [
                self._sum_tail(f"L{i}", teams, thr["coral"], z_map) for i in range(1, 5)
            ]
            if any(v is None for v in lv):
                out["rp_2"] = None
            else:
                c = self.bins["coop"].prob(teams) * self.bins["coop"].prob(opp)
                out["rp_2"] = c * _poibin_tail(lv, 3) + (1 - c) * _poibin_tail(lv, 4)
            out["rp_3"] = self._tail(self._robot_dist("barge", teams), thr["barge"])
        elif y == 2026:
            out["rp_1"] = self._sum_tail("fuel", teams, thr["energized"], z_map)
            out["rp_2"] = self._sum_tail("fuel", teams, thr["supercharged"], z_map)
            out["rp_3"] = self._traversal_2026(teams, thr["traversal"])
        return out

    def _traversal_2026(self, teams: Sequence[str], thr: float) -> float:
        """P(alliance TOWER points >= thr) with the 2-robot AUTO cap.

        Each robot has a joint AUTO/TELEOP state, so the AUTO and TELEOP climbs of one
        robot stay correlated. The convolution tracks (AUTO LEVEL 1 count, TELEOP points).
        """
        ch = self.robots["tower"]
        dists = []
        for t in teams:
            pr = ch.probs(t)
            d: Dict[Tuple[int, int], float] = {}
            for s, ps in enumerate(pr):
                key = (s // 4, _TOWER_TELEOP_PTS_2026[s % 4])
                d[key] = d.get(key, 0.0) + float(ps)
            dists.append(d)
        joint = _convolve(dists, lambda a, b: (a[0] + b[0], a[1] + b[1]))
        return float(
            sum(
                p
                for (na, tp), p in joint.items()
                if _TOWER_AUTO_PTS_2026 * min(na, _TOWER_AUTO_MAX_2026) + tp >= thr
            )
        )

    def _ensemble_2024(self, teams: Sequence[str]) -> float:
        ch = self.robots["stage"]
        dists = []
        for t in teams:
            pr = ch.probs(t)
            # (base stage points, onstage count)
            dists.append(
                {(0, 0): float(pr[0]), (1, 0): float(pr[1]), (3, 1): float(pr[2])}
            )
        joint = _convolve(dists, lambda a, b: (a[0] + b[0], a[1] + b[1]))
        total = 0.0
        for (base, k), pj in joint.items():
            if k < 2:
                continue
            need = 10 - base
            if need <= 0:
                total += pj
                continue
            ex = self.extra24[k]
            n = sum(ex.values())
            if n == 0:
                continue
            total += pj * sum(c for v, c in ex.items() if v >= need) / n
        return total

    # ---- final probability
    def _award_rate(
        self, key: str, table: Dict[str, List[float]], a0: float, b0: float
    ) -> float:
        a, b = table.get(key, (0.0, 0.0))
        return (a + a0) / (a + b + a0 + b0)

    def _flag_feat(
        self,
        key: str,
        teams: Sequence[str],
        z_map: Optional[Mapping[str, float]] = None,
    ) -> float:
        ch = self.flags.get(key)
        if ch is None or not ch.ready():
            return 0.0
        m, _ = ch.predict(teams, z_map)
        return _logit(min(max(m, 0.02), 0.98))

    def _cal_x(
        self,
        p_rule: float,
        extra: Optional[np.ndarray],
        key: str = "",
        teams: Sequence[str] = (),
        z_map: Optional[Mapping[str, float]] = None,
    ) -> np.ndarray:
        base = [1.0, _logit(p_rule) if self.p["rb_rule_feat"] else 0.0]
        if self.p["rb_flag"]:
            base.append(self._flag_feat(key, teams, z_map))
        x = np.array(base)
        if extra is None or not self.p["rb_mix"]:
            return x
        return np.concatenate([x, extra])

    def _new_cal(self, dim: int) -> OnlineLogit:
        """Prior calibration model: weight 1 on logit p_rule, 0 on the other inputs."""
        pv = self.p["rb_cal_pv"]
        mean = [0.0, 1.0] + [0.0] * (dim - 2)
        var = [pv, pv] + [self.p["rp_prior_var"]] * (dim - 2)
        return OnlineLogit(dim, var, self.p["rb_cal_q"], prior_mean=mean, q_all=True)

    def _cal_model(self, key: str, dim: int) -> OnlineLogit:
        """Stored calibration model for a key. The first call creates it (update path only)."""
        mdl = self.cal.get(key)
        if mdl is None:
            mdl = self._new_cal(dim)
            self.cal[key] = mdl
        return mdl

    def probs(
        self,
        keys: Sequence[str],
        tier: str,
        teams: Sequence[str],
        opp: Sequence[str],
        extra: Optional[np.ndarray] = None,
        z_map: Optional[Mapping[str, float]] = None,
    ) -> Dict[str, Optional[float]]:
        """Return final bonus probabilities, or None for keys without channel data."""
        pr = self.rule_probs(tier, teams, opp, z_map)
        out: Dict[str, Optional[float]] = {}
        for k in keys:
            p_rule = pr.get(k)
            if p_rule is None:
                out[k] = None
                continue
            x = self._cal_x(p_rule, extra, k, teams, z_map)
            p_met = self._cal_model_ro(k, x).prob(x)
            if self.p["rb_award"]:
                aw = self._award_rate(
                    k, self.award, self.p["rb_award_a"], self.p["rb_award_b"]
                )
                dn = self._award_rate(
                    k, self.deny, self.p["rb_award_a"], self.p["rb_award_b"]
                )
                p_met = p_met * (1.0 - dn) + (1.0 - p_met) * aw
            out[k] = min(max(p_met, 1e-4), 1.0 - 1e-4)
        return out

    def _cal_model_ro(self, key: str, x: np.ndarray) -> OnlineLogit:
        """Read-only access: an unseen key uses a fresh prior model that is not stored."""
        mdl = self.cal.get(key)
        return self._new_cal(len(x)) if mdl is None else mdl

    def update(
        self,
        tier: str,
        red: Sequence[str],
        blue: Sequence[str],
        bd_red: Mapping[str, Any],
        bd_blue: Mapping[str, Any],
        flags_red: Mapping[str, Any],
        flags_blue: Mapping[str, Any],
        extra_red: Optional[np.ndarray] = None,
        extra_blue: Optional[np.ndarray] = None,
        z_map: Optional[Mapping[str, float]] = None,
    ) -> None:
        """Train calibrators on pre-match rule probabilities, then update channels."""
        if not self.supported():
            return
        sides = (
            (red, blue, bd_red, bd_blue, flags_red, extra_red),
            (blue, red, bd_blue, bd_red, flags_blue, extra_blue),
        )
        # 1. Pre-match rule probabilities for both alliances, before any state change.
        pre = [self.rule_probs(tier, t, o, z_map) for t, o, *_ in sides]
        # 2. Calibrators and award rates.
        for (teams, opp, bd, obd, flags, extra), pr in zip(sides, pre):
            if not bd:
                continue
            met = rule_met(self.season, tier if self.p["rb_tier"] else "reg", bd, obd)
            for k, m in met.items():
                p_rule = pr.get(k)
                if p_rule is not None:
                    x = self._cal_x(p_rule, extra, k, teams, z_map)
                    self._cal_model(k, len(x)).update(x, float(m))
                f = flags.get(k) if isinstance(flags, Mapping) else None
                if f is None:
                    continue
                f = 1 if f else 0
                if m == 0:
                    a, b = self.award.get(k, (0.0, 0.0))
                    self.award[k] = [a + f, b + (1 - f)]
                else:
                    a, b = self.deny.get(k, (0.0, 0.0))
                    self.deny[k] = [a + (1 - f), b + f]
        # 3. Channels.
        zp = float(self.p.get("rb_z_prior", 0.0))
        for teams, opp, bd, obd, flags, extra in sides:
            if not bd:
                continue
            if self.p["rb_flag"] and isinstance(flags, Mapping):
                for k, f in flags.items():
                    if f is None:
                        continue
                    ch = self.flags.get(k)
                    if ch is None:
                        ch = SumChannel(
                            self.p["rb_q_frac"], self.p["rb_prior_share"], zp
                        )
                        self.flags[k] = ch
                    ch.update(teams, 1.0 if f else 0.0, z_map)
            for name, y in _sum_obs(self.season, bd).items():
                self.sums[name].update(teams, float(y), z_map)
            robot = _robot_obs(self.season, bd, len(teams))
            for name, states in robot.items():
                for t, s in zip(teams, states):
                    self.robots[name].update(t, s)
            for name, y in _bin_obs(self.season, bd, robot).items():
                self.bins[name].update(teams, y)
            if self.season == 2024 and "stage" in robot:
                base = sum(_ROBOT_DEFS[2024]["stage"][2][s] for s in robot["stage"])
                k = sum(1 for s in robot["stage"] if s == 2)
                ex = int((bd.get("endGameTotalStagePoints") or 0) - base)
                self.extra24[k][ex] = self.extra24[k].get(ex, 0) + 1

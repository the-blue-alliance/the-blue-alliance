"""Data adapter layer translating TBA NDB Models (Match, Event)
to SOTA prediction contracts (MatchContext, MatchOutcome).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.common.models.event import Event
    from backend.common.models.match import Match

    from .context import MatchContext
    from .outcome import MatchOutcome


# Progression ordering for competition levels:
# qm (Qualification) -> ef (Eighth-finals) -> qf (Quarter-finals) -> sf (Semi-finals) -> f (Finals)
COMP_LEVEL_ORDER: Dict[str, int] = {
    "qm": 1,
    "ef": 2,
    "qf": 3,
    "sf": 4,
    "f": 5,
}

# Standard mapping of season-specific TBA score_breakdown bonus RP fields to canonical keys
SEASON_BONUS_RP_FIELDS: Dict[int, List[Tuple[str, List[str]]]] = {
    2016: [
        (
            "rp_1",
            [
                "teleopDefensesBreached",
                "defensesBreached",
                "teleopDefensesBreachedRankingPoint",
            ],
        ),
        (
            "rp_2",
            ["teleopTowerCaptured", "towerCaptured", "teleopTowerCapturedRankingPoint"],
        ),
    ],
    2017: [
        (
            "rp_1",
            [
                "kPaRankingPoint",
                "kpaRankingPoint",
                "kPaBonusRankingPointAchieved",
                "kpaBonusRankingPointAchieved",
                "kPaRankingPointAchieved",
            ],
        ),
        (
            "rp_2",
            [
                "rotorRankingPoint",
                "rotorBonusRankingPointAchieved",
                "rotorRankingPointAchieved",
                "rotor4Engaged",
            ],
        ),
    ],
    2018: [
        ("rp_1", ["autoQuestRankingPoint", "autoQuestRankingPointAchieved"]),
        ("rp_2", ["faceTheBossRankingPoint", "faceTheBossRankingPointAchieved"]),
    ],
    2019: [
        (
            "rp_1",
            [
                "completeRocketRankingPoint",
                "completeRocketRankingPointAchieved",
                "rocketRankingPoint",
            ],
        ),
        (
            "rp_2",
            [
                "habDockingRankingPoint",
                "habDockingRankingPointAchieved",
                "habRankingPoint",
            ],
        ),
    ],
    2020: [
        (
            "rp_1",
            ["shieldOperationalRankingPoint", "shieldOperationalRankingPointAchieved"],
        ),
        (
            "rp_2",
            ["shieldEnergizedRankingPoint", "shieldEnergizedRankingPointAchieved"],
        ),
    ],
    2021: [
        (
            "rp_1",
            ["shieldOperationalRankingPoint", "shieldOperationalRankingPointAchieved"],
        ),
        (
            "rp_2",
            ["shieldEnergizedRankingPoint", "shieldEnergizedRankingPointAchieved"],
        ),
    ],
    2022: [
        ("rp_1", ["cargoBonusRankingPoint", "cargoBonusRankingPointAchieved"]),
        ("rp_2", ["hangarBonusRankingPoint", "hangarBonusRankingPointAchieved"]),
    ],
    2023: [
        ("rp_1", ["sustainabilityBonusAchieved", "sustainabilityBonusRankingPoint"]),
        ("rp_2", ["activationBonusAchieved", "activationBonusRankingPoint"]),
    ],
    2024: [
        ("rp_1", ["melodyBonusAchieved", "melodyBonusRankingPoint"]),
        ("rp_2", ["ensembleBonusAchieved", "ensembleBonusRankingPoint"]),
    ],
    2025: [
        ("rp_1", ["autoBonusAchieved", "autoRankingPoint", "autoBonusRankingPoint"]),
        ("rp_2", ["coralBonusAchieved", "coralRankingPoint", "coralBonusRankingPoint"]),
        ("rp_3", ["bargeBonusAchieved", "bargeRankingPoint", "bargeBonusRankingPoint"]),
    ],
    2026: [
        (
            "rp_1",
            [
                "energizedAchieved",
                "energizedRankingPoint",
                "autoBonusAchieved",
                "autoRankingPoint",
                "melodyBonusAchieved",
                "rp_1",
            ],
        ),
        (
            "rp_2",
            [
                "superchargedAchieved",
                "superchargedRankingPoint",
                "coralBonusAchieved",
                "coralRankingPoint",
                "ensembleBonusAchieved",
                "rp_2",
            ],
        ),
        (
            "rp_3",
            [
                "traversalAchieved",
                "traversalRankingPoint",
                "bargeBonusAchieved",
                "bargeRankingPoint",
                "rp_3",
            ],
        ),
    ],
}


def _to_binary_int(val: Any) -> int:
    """Normalize boolean, numeric, or string flag to binary 1 or 0."""
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return 1 if (math.isfinite(val) and val > 0) else 0
    if isinstance(val, str):
        return 1 if val.strip().lower() in ("true", "1", "yes", "y") else 0
    return 0


def extract_canonical_bonus_rps(
    season: int,
    alliance_breakdown: Optional[Dict[str, Any]],
) -> Dict[str, int]:
    """Extract canonical binary bonus ranking points ('rp_1', 'rp_2', 'rp_3') for an alliance."""
    if (
        season < 2016
        or not isinstance(alliance_breakdown, dict)
        or not alliance_breakdown
    ):
        return {}

    bonuses: Dict[str, int] = {}
    max_idx = 3 if season >= 2025 else 2

    lower_breakdown: Dict[str, Any] = {
        str(k).lower(): v for k, v in alliance_breakdown.items()
    }

    # Direct canonical keys check
    has_direct_keys = any(
        k in lower_breakdown for k in ("rp_1", "rp_2", "rp_3", "rp1", "rp2", "rp3")
    )
    if has_direct_keys:
        for idx in range(1, max_idx + 1):
            canon_k = f"rp_{idx}"
            alt_k = f"rp{idx}"
            if canon_k in alliance_breakdown:
                bonuses[canon_k] = _to_binary_int(alliance_breakdown[canon_k])
            elif canon_k in lower_breakdown:
                bonuses[canon_k] = _to_binary_int(lower_breakdown[canon_k])
            elif alt_k in alliance_breakdown:
                bonuses[canon_k] = _to_binary_int(alliance_breakdown[alt_k])
            elif alt_k in lower_breakdown:
                bonuses[canon_k] = _to_binary_int(lower_breakdown[alt_k])
        return bonuses

    # Season mapping lookup
    field_mappings = SEASON_BONUS_RP_FIELDS.get(season)
    if field_mappings is not None:
        for canon_k, candidates in field_mappings:
            for cand in candidates:
                cand_lower = cand.lower()
                if cand in alliance_breakdown and alliance_breakdown[cand] is not None:
                    bonuses[canon_k] = _to_binary_int(alliance_breakdown[cand])
                    break
                elif (
                    cand_lower in lower_breakdown
                    and lower_breakdown[cand_lower] is not None
                ):
                    bonuses[canon_k] = _to_binary_int(lower_breakdown[cand_lower])
                    break
        return bonuses

    # Fallback for unmapped seasons
    for k, v in alliance_breakdown.items():
        k_lower = str(k).lower()
        if "rp_1" in k_lower or "bonus_1" in k_lower:
            bonuses["rp_1"] = _to_binary_int(v)
        elif "rp_2" in k_lower or "bonus_2" in k_lower:
            bonuses["rp_2"] = _to_binary_int(v)
        elif "rp_3" in k_lower or "bonus_3" in k_lower:
            bonuses["rp_3"] = _to_binary_int(v)

    return bonuses


def to_match_context(match: Match, event: Event) -> MatchContext:
    """Convert TBA Match and Event NDB entities to an immutable MatchContext."""
    from .context import MatchContext

    return MatchContext.from_tba_match(match, event)


def to_match_outcome(match: Match, event: Event) -> Optional[MatchOutcome]:
    """Convert a played TBA Match and Event NDB entities to a MatchOutcome."""
    from .outcome import MatchOutcome

    return MatchOutcome.from_tba_match(match, event)

from types import SimpleNamespace
from typing import Any, cast, Dict, List, Optional

from backend.common.models.event import Event
from backend.common.models.match import Match


def fake_match(
    red_score: int,
    blue_score: int,
    red_breakdown: Optional[Dict[str, Any]] = None,
    blue_breakdown: Optional[Dict[str, Any]] = None,
    year: int = 2024,
    key_name: str = "2024test_qm1",
    comp_level: str = "qm",
) -> Match:
    """A lightweight stand-in for a Match, for calculator edge cases."""
    score_breakdown = (
        {"red": red_breakdown or {}, "blue": blue_breakdown or {}}
        if red_breakdown is not None or blue_breakdown is not None
        else None
    )
    return cast(
        Match,
        SimpleNamespace(
            key_name=key_name,
            year=year,
            comp_level=comp_level,
            has_been_played=red_score != -1 and blue_score != -1,
            alliances={
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": red_score},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": blue_score},
            },
            score_breakdown=score_breakdown,
        ),
    )


def fake_event(matches: List[Match], **kwargs: Any) -> Event:
    return cast(Event, SimpleNamespace(matches=matches, **kwargs))

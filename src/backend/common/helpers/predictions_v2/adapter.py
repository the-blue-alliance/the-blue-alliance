"""Conversion of TBA matches and events into predictor inputs.

Which matches enter a season's stream:

* Event types 0-6 (regional through FOC): train entries. The model predicts the match,
  then learns from its result.
* Offseason and preseason events: forecast-only entries. The model predicts the match but
  never learns from it.
* Remote and unlabeled events: not in the stream.

Practice matches and unplayed matches are never entries.
"""

import calendar
import datetime
import enum
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2.model.bonus import BONUS_RP_FIELDS
from backend.common.helpers.predictions_v2.model.types import (
    AllianceBreakdown,
    MatchContext,
    MatchOutcome,
)
from backend.common.helpers.predictions_v2.ordering import (
    event_block_order,
    MatchSlot,
)
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
from backend.common.models.match import Match


@enum.unique
class EntryKind(str, enum.Enum):
    TRAIN = "train"
    FORECAST = "forecast"


TRAIN_EVENT_TYPES = frozenset(
    {
        EventType.REGIONAL,
        EventType.DISTRICT,
        EventType.DISTRICT_CMP,
        EventType.CMP_DIVISION,
        EventType.CMP_FINALS,
        EventType.DISTRICT_CMP_DIVISION,
        EventType.FOC,
    }
)
FORECAST_EVENT_TYPES = frozenset({EventType.OFFSEASON, EventType.PRESEASON})


def entry_kind(event: Event) -> Optional[EntryKind]:
    """How the event's matches enter the stream, or None if they do not."""
    event_type = event.event_type_enum
    if event_type in TRAIN_EVENT_TYPES:
        return EntryKind.TRAIN
    if event_type in FORECAST_EVENT_TYPES:
        return EntryKind.FORECAST
    return None


def is_stream_match(match: Match) -> bool:
    """A played, non-practice match."""
    return match.comp_level != CompLevel.PM and match.has_been_played


def to_match_context(match: Match, event: Event) -> MatchContext:
    alliances = match.alliances
    return MatchContext(
        match_key=match.key_name,
        event_key=event.key_name,
        event_type=EventType(event.event_type_enum),
        comp_level=CompLevel(match.comp_level),
        red_teams=tuple(alliances[AllianceColor.RED]["teams"]),
        blue_teams=tuple(alliances[AllianceColor.BLUE]["teams"]),
    )


def _flag(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if value > 0 else 0
    if isinstance(value, str):
        return 1 if value.strip().lower() in ("true", "1", "yes", "y") else 0
    return 0


def bonus_rps(year: Year, breakdown: Optional[AllianceBreakdown]) -> Dict[str, int]:
    """Bonus ranking points earned, keyed "rp_1" .. "rp_3". A missing flag is left out:
    a field that is absent is not a bonus that was missed."""
    if not breakdown:
        return {}
    out: Dict[str, int] = {}
    for i, name in enumerate(BONUS_RP_FIELDS.get(year, ())):
        value = breakdown.get(name)
        if value is not None:
            out[f"rp_{i + 1}"] = _flag(value)
    return out


def to_match_outcome(match: Match) -> MatchOutcome:
    """The result of a played match."""
    alliances = match.alliances
    red, blue = alliances[AllianceColor.RED], alliances[AllianceColor.BLUE]
    red_score, blue_score = int(red["score"]), int(blue["score"])
    # The alliance that advanced wins a tied playoff match decided by a tiebreaker.
    winner = match.winning_alliance
    if winner == AllianceColor.RED:
        red_win = 1.0
    elif winner == AllianceColor.BLUE:
        red_win = 0.0
    elif red_score != blue_score:
        red_win = 1.0 if red_score > blue_score else 0.0
    else:
        red_win = 0.5
    breakdown = match.score_breakdown
    red_bd = breakdown.get(AllianceColor.RED) if breakdown else None
    blue_bd = breakdown.get(AllianceColor.BLUE) if breakdown else None
    return MatchOutcome(
        red_score=red_score,
        blue_score=blue_score,
        red_win=red_win,
        red_breakdown=red_bd,
        blue_breakdown=blue_bd,
        red_bonus_rps=bonus_rps(match.year, red_bd),
        blue_bonus_rps=bonus_rps(match.year, blue_bd),
        red_dqs=tuple(red["dqs"]),
        blue_dqs=tuple(blue["dqs"]),
    )


def outcome_fingerprint(match: Match) -> str:
    """Hash of everything the model reads from a played match. A change means the
    result was corrected."""
    alliances = match.alliances
    payload = {
        "comp_level": match.comp_level,
        "alliances": {
            color: {
                "teams": alliances[color]["teams"],
                "score": alliances[color]["score"],
                "dqs": alliances[color]["dqs"],
            }
            for color in (AllianceColor.RED, AllianceColor.BLUE)
        },
        "winner": match.winning_alliance,
        "breakdown": match.score_breakdown,
    }
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()


def _unix(t: Optional[datetime.datetime]) -> Optional[int]:
    """The same conversion as the APIv3 match converter (server local time is UTC)."""
    if t is None:
        return None
    try:
        return int(time.mktime(t.timetuple()))
    except (OverflowError, ValueError):
        # Some old matches carry placeholder times (1900-01-01) that the platform's
        # mktime cannot convert.
        return calendar.timegm(t.timetuple())


def _day_epoch(d: Optional[datetime.datetime]) -> Optional[int]:
    return calendar.timegm(d.date().timetuple()) if d is not None else None


def match_slot(match: Match, event: Event) -> MatchSlot:
    """The match's place in the event-block order."""
    actual = _unix(match.actual_time)
    return MatchSlot(
        match_key=match.key_name,
        event_key=event.key_name,
        year=event.year,
        comp_level=CompLevel(match.comp_level),
        set_number=match.set_number,
        match_number=match.match_number,
        time=actual if actual is not None else _unix(match.time),
        event_start=_day_epoch(event.start_date),
        event_end=_day_epoch(event.end_date),
    )


@dataclass(frozen=True)
class StreamItem:
    """One played match, ready for the predictor."""

    kind: EntryKind
    slot: MatchSlot
    context: MatchContext
    outcome: MatchOutcome
    fingerprint: str

    @property
    def year(self) -> Year:
        return self.slot.year


def stream_item(match: Match, event: Event) -> Optional[StreamItem]:
    kind = entry_kind(event)
    if kind is None or not is_stream_match(match):
        return None
    return StreamItem(
        kind=kind,
        slot=match_slot(match, event),
        context=to_match_context(match, event),
        outcome=to_match_outcome(match),
        fingerprint=outcome_fingerprint(match),
    )


def build_stream(
    events: Mapping[EventKey, Event], matches: Iterable[Match]
) -> List[StreamItem]:
    """Stream entries of the matches, in event-block order."""
    items: List[StreamItem] = []
    for match in matches:
        event = events.get(match.event_key_name)
        item = stream_item(match, event) if event is not None else None
        if item is not None:
            items.append(item)
    return [items[i] for i in event_block_order([it.slot for it in items])]

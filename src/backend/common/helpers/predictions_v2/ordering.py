"""Event-block order of a season's matches.

1. Inside an event, matches follow bracket order: qualifications by match number,
   best-of-3 playoffs (before 2023) round by round, and double-elimination playoffs (2023
   and later) set by set.
2. Across events, a per-event interleave time orders concurrent events. A timed event uses
   the running maximum of match start times (actual time, else scheduled time) in bracket
   order. A match without a time takes the previous match's value, and leading untimed
   matches take the earliest time of the event. An untimed event spreads its matches
   evenly between its start date and the end of its end date.
3. Season is the primary key, so each season is one contiguous block.

The sort key of a match depends only on its own event's matches.
"""

import calendar
import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from backend.common.consts.comp_level import COMP_LEVELS_PLAY_ORDER, CompLevel
from backend.common.models.keys import EventKey, MatchKey, Year

DOUBLE_ELIM_FIRST_YEAR = 2023
_DAY = 86400

BracketKey = Tuple[int, int, int]
SortKey = Tuple[Year, int, EventKey, BracketKey]


@dataclass(frozen=True)
class MatchSlot:
    match_key: MatchKey
    event_key: EventKey
    year: Year
    comp_level: CompLevel
    set_number: int
    match_number: int
    # Unix seconds: actual start, else scheduled start.
    time: Optional[int]
    # Unix seconds of the event's start and end dates (UTC midnight).
    event_start: Optional[int]
    event_end: Optional[int]


def bracket_key(
    year: Year, comp_level: CompLevel, set_number: int, match_number: int
) -> BracketKey:
    """Play order inside an event. A replayed match has a higher match number in the
    same set, so it follows the original."""
    rank = COMP_LEVELS_PLAY_ORDER[comp_level]
    if comp_level == CompLevel.QM:
        return (rank, match_number, set_number)
    if year >= DOUBLE_ELIM_FIRST_YEAR:
        return (rank, set_number, match_number)
    return (rank, match_number, set_number)


def _event_bounds(slot: MatchSlot) -> Tuple[int, int]:
    """(start, end) of an event. Without dates: March 1 of the season, 3 days."""
    start = slot.event_start
    if start is None:
        start = calendar.timegm(datetime.date(slot.year, 3, 1).timetuple())
    end = slot.event_end
    if end is None or end < start:
        end = start + 2 * _DAY
    return start, end + _DAY


def event_block_keys(slots: Sequence[MatchSlot]) -> List[SortKey]:
    """The sort key of each slot, in input order."""
    groups: Dict[EventKey, List[int]] = {}
    brackets = [
        bracket_key(s.year, s.comp_level, s.set_number, s.match_number) for s in slots
    ]
    for i, s in enumerate(slots):
        groups.setdefault(s.event_key, []).append(i)
    keys: Dict[int, SortKey] = {}
    for event_key, idxs in groups.items():
        idxs.sort(key=lambda i: (brackets[i], _time_or_inf(slots[i].time)))
        known = [t for t in (slots[i].time for i in idxs) if t is not None]
        if known:
            prev = min(known)
            for i in idxs:
                t = slots[i].time
                if t is not None and t > prev:
                    prev = t
                keys[i] = (slots[i].year, prev, event_key, brackets[i])
        else:
            start, end = _event_bounds(slots[idxs[0]])
            n = len(idxs)
            span = end - start
            for pos, i in enumerate(idxs):
                keys[i] = (
                    slots[i].year,
                    start + (span * pos) // n,
                    event_key,
                    brackets[i],
                )
    return [keys[i] for i in range(len(slots))]


def _time_or_inf(t: Optional[int]) -> float:
    return float("inf") if t is None else float(t)


def event_block_order(slots: Sequence[MatchSlot]) -> List[int]:
    """Indices of ``slots`` in event-block order."""
    keys = event_block_keys(slots)
    return sorted(range(len(slots)), key=lambda i: keys[i])

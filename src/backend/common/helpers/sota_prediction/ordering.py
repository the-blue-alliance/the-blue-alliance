"""Chronological replay ordering for the benchmark replay stream.

Default order (modes 'auto' and 'hybrid') is the two-level event-block sort:
1. Inside an event, matches follow bracket order (`bracket_key`). Qualifications
   play by match number. Best-of-3 playoffs (before 2023) play round by round.
   Double-elimination playoffs (2023 and later) play set by set.
2. Across events, a per-event interleave time orders concurrent events. A timed
   event uses the running maximum of match start times (actual_time, else
   scheduled time) in bracket order. An untimed event spreads its matches evenly
   between start_date and end_date. post_result_time is never used.
3. Season is the primary key, so each season forms one contiguous block.

`assert_stream_invariants` checks the result before replay.

Legacy modes 'timed' (global timestamp sort) and 'untimed' (round-by-round
progression key) stay available for explicit callers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

# Numerical progression ranking for competition levels:
# qm (Qualification) -> ef (Eighth-finals) -> qf (Quarter-finals) -> sf (Semi-finals) -> f (Finals)
COMP_LEVEL_PROGRESSION: Dict[str, int] = {
    "qm": 0,
    "ef": 1,
    "qf": 2,
    "sf": 3,
    "f": 4,
}

UNKNOWN_COMP_LEVEL_RANK: int = 99


def _to_timestamp(val: Any) -> Optional[int]:
    if val is None:
        return None
    if hasattr(val, "timestamp"):
        return int(val.timestamp())
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def get_effective_match_time(match: Any) -> Optional[int]:
    """Extract effective match start timestamp: actual_time fallback to scheduled time.

    Strictly ignores post_result_time to prevent lookahead bias.
    Supports TBAMatch, MatchContext, dict, and duck-typed objects.
    """
    if match is None:
        return None

    if isinstance(match, dict):
        actual = _to_timestamp(match.get("actual_time"))
        if actual is not None:
            return actual
        sched = _to_timestamp(match.get("time"))
        if sched is not None:
            return sched
        return None

    # Check for actual_time attribute
    actual = _to_timestamp(getattr(match, "actual_time", None))
    if actual is not None:
        return actual

    # MatchContext exposes scheduled_time
    sched = _to_timestamp(getattr(match, "scheduled_time", None))
    if sched is not None:
        return sched

    # TBAMatch exposes time
    sched_time = _to_timestamp(getattr(match, "time", None))
    if sched_time is not None:
        return sched_time

    return None


def get_comp_level_rank(comp_level: Optional[str]) -> int:
    """Map competition stage string to numerical progression rank.

    'qm' -> 0, 'ef' -> 1, 'qf' -> 2, 'sf' -> 3, 'f' -> 4, unknown -> 99.
    Case-insensitive and whitespace-tolerant.
    """
    if not comp_level:
        return UNKNOWN_COMP_LEVEL_RANK
    return COMP_LEVEL_PROGRESSION.get(
        str(comp_level).strip().lower(), UNKNOWN_COMP_LEVEL_RANK
    )


def get_match_identifiers(match: Any) -> Tuple[str, str, int, int]:
    """Extract (event_key, comp_level, set_number, match_number) from match object or dict."""
    if isinstance(match, dict):
        event_key = str(match.get("event_key") or "")
        comp_level = str(match.get("comp_level") or "qm")
        set_number = int(match.get("set_number", 1) or 1)
        match_number = int(match.get("match_number", 1) or 1)
    else:
        event_key = str(getattr(match, "event_key", "") or "")
        comp_level = str(getattr(match, "comp_level", "qm") or "qm")
        set_number = int(getattr(match, "set_number", 1) or 1)
        match_number = int(getattr(match, "match_number", 1) or 1)

    return event_key, comp_level, set_number, match_number


def get_match_season(
    match: Any,
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> int:
    """Extract 4-digit season year from match or event context.

    Lookup hierarchy:
    1. events map or sequence matching match.event_key (year attribute or dict field)
    2. match.event_metadata (if MatchContext or match has event_metadata)
    3. event_key prefix (e.g. '2024casj' -> 2024)
    4. match_key prefix (e.g. '2024casj_qm1' -> 2024)
    5. fallback 2000
    """
    event_key, _, _, _ = get_match_identifiers(match)
    if events:
        if isinstance(events, Mapping) and event_key in events:
            ev = events[event_key]
            y = (
                getattr(ev, "year", None)
                if not isinstance(ev, dict)
                else ev.get("year")
            )
            if y is not None:
                return int(y)
        elif isinstance(events, Sequence):
            for ev in events:
                ek = (
                    getattr(ev, "key", None)
                    if not isinstance(ev, dict)
                    else ev.get("key")
                )
                if ek == event_key:
                    y = (
                        getattr(ev, "year", None)
                        if not isinstance(ev, dict)
                        else ev.get("year")
                    )
                    if y is not None:
                        return int(y)
                    break

    meta = getattr(match, "event_metadata", None)
    if meta is None and isinstance(match, dict):
        meta = match.get("event_metadata")
    if meta is not None:
        y = (
            getattr(meta, "year", None)
            if not isinstance(meta, dict)
            else meta.get("year")
        )
        if y is not None:
            return int(y)

    if len(event_key) >= 4 and event_key[:4].isdigit():
        return int(event_key[:4])

    match_key = getattr(match, "key", None) or (
        match.get("key") if isinstance(match, dict) else None
    )
    if match_key and len(str(match_key)) >= 4 and str(match_key)[:4].isdigit():
        return int(str(match_key)[:4])

    return 2000


def is_timed_match(match: Any) -> bool:
    """Return True if match has a non-null actual_time or scheduled time timestamp."""
    return get_effective_match_time(match) is not None


def get_event_week_or_date(
    match: Any,
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> int:
    """Extract normalized integer competition week (or date-derived ordinal).

    Lookup hierarchy:
    1. events map or sequence matching match.event_key
    2. match.event_metadata (if MatchContext or match has event_metadata)
    3. parsed from event_key (e.g. 'cmp' suffix defaults to week 8)
    4. normalized_week logic: Championship types (3, 4) -> 8, Offseason (99) -> 10,
       Preseason (100) -> -1.
    5. start_date ISO calendar week or relative offset.
    Fallback: 0.
    """
    event_key, _, _, _ = get_match_identifiers(match)

    ev = None
    if events is not None:
        if isinstance(events, Mapping):
            ev = events.get(event_key)
        elif isinstance(events, Sequence):
            ev = next(
                (
                    e
                    for e in events
                    if getattr(e, "key", getattr(e, "event_key", None)) == event_key
                    or (
                        isinstance(e, dict)
                        and (
                            e.get("key") == event_key or e.get("event_key") == event_key
                        )
                    )
                ),
                None,
            )

    meta = None
    if getattr(match, "event_metadata", None):
        meta = getattr(match, "event_metadata")
    elif isinstance(match, dict) and match.get("event_metadata"):
        meta = match.get("event_metadata")

    week = None
    event_type = None
    start_date = None

    if ev is not None:
        if isinstance(ev, dict):
            week = ev.get("week")
            event_type = ev.get("event_type")
            start_date = ev.get("start_date")
        else:
            if (
                hasattr(ev, "normalized_week")
                and getattr(ev, "normalized_week", None) is not None
            ):
                return int(ev.normalized_week)
            week = getattr(ev, "week", None)
            event_type = getattr(ev, "event_type", None)
            start_date = getattr(ev, "start_date", None)

    if week is None and meta is not None:
        if meta.get("normalized_week") is not None:
            return int(meta["normalized_week"])
        week = meta.get("week")
        event_type = meta.get("event_type")
        start_date = meta.get("start_date")

    if week is not None:
        return int(week)

    if event_type in (3, 4) or "cmp" in event_key.lower():
        return 8

    if event_type == 100:
        return -1

    if event_type == 99:
        return 10

    if start_date:
        try:
            dt = datetime.fromisoformat(str(start_date)).date()
            return dt.isocalendar()[1]
        except Exception:
            pass

    return 0


def timed_match_sort_key(match: Any) -> Tuple[int, str, int, int, int]:
    """Construct deterministic 5-tuple sort key for timed matches:

    (effective_timestamp, event_key, comp_level_rank, set_number, match_number).

    Raises ValueError if match has no effective start time.
    """
    ts = get_effective_match_time(match)
    if ts is None:
        event_key, comp_level, set_num, match_num = get_match_identifiers(match)
        raise ValueError(
            f"Match '{event_key}_{comp_level}{set_num}m{match_num}' has no effective start time "
            f"and cannot be ordered with timed_match_sort_key."
        )

    event_key, comp_level, set_number, match_number = get_match_identifiers(match)
    comp_rank = get_comp_level_rank(comp_level)
    return (ts, event_key, comp_rank, set_number, match_number)


def untimed_match_sort_key(
    match: Any,
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> Tuple[int, int, int, int, int, str]:
    """Construct deterministic 6-tuple progression sort key for untimed matches:

    (season, event_week_or_date, comp_level_rank, match_number, set_number, event_key).

    Interleaves round-by-round across concurrent events within each season.
    """
    season = get_match_season(match, events)
    event_week = get_event_week_or_date(match, events)
    event_key, comp_level, set_number, match_number = get_match_identifiers(match)
    comp_rank = get_comp_level_rank(comp_level)
    return (season, event_week, comp_rank, match_number, set_number, event_key)


def hybrid_match_sort_key(
    match: Any,
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> Tuple[int, str, int, int, int]:
    """Construct unified 5-tuple sort key for hybrid streams (mixed timed/untimed).

    Uses real effective timestamp for timed matches, and calculates an aligned
    synthetic timestamp for untimed matches anchored to event date/week and
    progression index.
    """
    event_key, comp_level, set_number, match_number = get_match_identifiers(match)
    comp_rank = get_comp_level_rank(comp_level)

    ts = get_effective_match_time(match)
    if ts is not None:
        return (ts, event_key, comp_rank, set_number, match_number)

    # Calculate synthetic timeline anchor
    year = get_match_season(match, events)
    week = get_event_week_or_date(match, events)

    # Base epoch: March 1 of season year + week offset
    base_epoch = (
        int(datetime(year, 3, 1, 9, 0, tzinfo=timezone.utc).timestamp())
        + week * 7 * 86400
    )

    stage_offset = comp_rank * 86400
    match_offset = match_number * 300
    set_offset = set_number * 60
    synth_ts = base_epoch + stage_offset + match_offset + set_offset

    return (synth_ts, event_key, comp_rank, set_number, match_number)


def sort_timed_matches(matches: Sequence[Any]) -> List[Any]:
    """Sort a sequence of timed matches using the timed multi-key sort."""
    return sorted(matches, key=timed_match_sort_key)


def sort_untimed_matches(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> List[Any]:
    """Sort a sequence of untimed matches using round-by-round tournament progression interleaving."""
    return sorted(matches, key=lambda m: untimed_match_sort_key(m, events))


# -----------------------------------------------------------------------------
# Event-block ordering (audit F4, F5)
# -----------------------------------------------------------------------------

# First season in which FRC playoffs used the double-elimination bracket
# (sf sets 1-13, then f). Earlier seasons used best-of-3 rounds.
DOUBLE_ELIM_FIRST_SEASON: int = 2023


def bracket_key(
    season: int, comp_level: Optional[str], set_number: int, match_number: int
) -> Tuple[int, int, int]:
    """Return the within-event play order key for one match.

    - Qualifications play in match-number order.
    - Best-of-3 playoffs (before 2023) play round by round: qf1m1, qf2m1, ..., qf1m2.
    - Double-elimination playoffs (2023 and later) play set by set: sf1m1, sf2m1, ..., sf13m1.
      A replayed match has a higher match number in the same set, so it follows the original.
    """
    rank = get_comp_level_rank(comp_level)
    if rank == 0:
        return (0, match_number, set_number)
    if season >= DOUBLE_ELIM_FIRST_SEASON:
        return (rank, set_number, match_number)
    return (rank, match_number, set_number)


def _event_field(ev: Any, name: str) -> Any:
    if ev is None:
        return None
    if isinstance(ev, dict):
        return ev.get(name)
    return getattr(ev, name, None)


def _date_epoch(value: Any) -> Optional[int]:
    if not value:
        return None
    if isinstance(value, datetime):
        return int(
            datetime(
                value.year, value.month, value.day, tzinfo=timezone.utc
            ).timestamp()
        )
    from datetime import date

    if isinstance(value, date):
        return int(
            datetime(
                value.year, value.month, value.day, tzinfo=timezone.utc
            ).timestamp()
        )
    try:
        d = datetime.fromisoformat(str(value)).date()
    except (ValueError, TypeError):
        return None
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def event_anchor_bounds(ev: Any, season: int) -> Tuple[int, int]:
    """Return (start, end) epoch seconds for an event from its start_date and end_date.

    The end bound is the end of the end_date day. Events without dates fall back to
    March 1 of the season, with a 3-day span.
    """
    start = _date_epoch(_event_field(ev, "start_date"))
    end = _date_epoch(_event_field(ev, "end_date"))
    if start is None:
        start = int(datetime(season, 3, 1, tzinfo=timezone.utc).timestamp())
    if end is None or end < start:
        end = start + 2 * 86400
    return start, end + 86400


def _normalize_event_lookup(
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]],
) -> Dict[str, Any]:
    if not events:
        return {}
    if isinstance(events, Mapping):
        return dict(events)
    out: Dict[str, Any] = {}
    for e in events:
        k = _event_field(e, "key") or _event_field(e, "event_key")
        if k:
            out[str(k)] = e
    return out


def event_block_sort_keys(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> List[Tuple[int, int, str, Tuple[int, int, int]]]:
    """Compute the event-block sort key for each match, in input order.

    Key: (season, interleave_time, event_key, bracket_key).

    1. Inside an event, matches follow `bracket_key`. Timestamps never reorder them.
    2. Each event decides on its own whether it is timed.
       - Timed event: interleave_time is the running maximum of the effective start
         time (actual_time, else scheduled time) along bracket order. A match without
         a time inherits the previous match's value. Leading untimed matches take
         the earliest known time in the event.
       - Untimed event: matches are spread evenly between start_date and end_date.
    3. Across events, interleave_time orders concurrent events. Season is the primary
       key, so each season forms one contiguous block.
    """
    lookup = _normalize_event_lookup(events)
    groups: Dict[str, List[int]] = {}
    info: List[Tuple[int, str, Tuple[int, int, int], Optional[int]]] = []
    for idx, m in enumerate(matches):
        event_key, comp_level, set_number, match_number = get_match_identifiers(m)
        season = get_match_season(m, lookup or None)
        bkey = bracket_key(season, comp_level, set_number, match_number)
        info.append((season, event_key, bkey, get_effective_match_time(m)))
        groups.setdefault(event_key, []).append(idx)

    keys: List[Any] = [None] * len(info)
    for event_key, idxs in groups.items():
        # Bracket order first. Effective time breaks ties only for inputs that lack
        # distinct identifiers (for example, synthetic matches without match numbers).
        idxs.sort(
            key=lambda i: (
                info[i][2],
                info[i][3] if info[i][3] is not None else float("inf"),
            )
        )
        season = info[idxs[0]][0]
        known = [info[i][3] for i in idxs if info[i][3] is not None]
        if known:
            prev = min(known)
            for i in idxs:
                t = info[i][3]
                if t is not None and t > prev:
                    prev = t
                keys[i] = (info[i][0], prev, event_key, info[i][2])
        else:
            start, end = event_anchor_bounds(lookup.get(event_key), season)
            n = len(idxs)
            span = end - start
            for pos, i in enumerate(idxs):
                keys[i] = (info[i][0], start + (span * pos) // n, event_key, info[i][2])
    return keys


def sort_event_block(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> List[Any]:
    """Sort matches with the two-level event-block order. See `event_block_sort_keys`."""
    match_list = list(matches)
    keys = event_block_sort_keys(match_list, events)
    order = sorted(range(len(match_list)), key=lambda i: keys[i])
    return [match_list[i] for i in order]


def _rev_str(s: str) -> Tuple[int, ...]:
    """Invert string codepoints for descending lexicographical tie-breaking."""
    return tuple(-ord(c) for c in s) + (0,)


def _extract_week_and_stage(
    match: Any,
    lookup: Optional[Mapping[str, Any]] = None,
) -> Tuple[int, int]:
    """Extract (normalized_week, stage_rank) for week and stage chronological grouping.

    Within a given normalized_week, regional/district/division events (types 0, 1, 3, 5)
    have stage_rank 0 and precede culminating finals (DCMP finals=2, Einstein=4, FoC=6)
    which have stage_rank 1.
    """
    event_key, _, _, _ = get_match_identifiers(match)
    ev = lookup.get(event_key) if lookup else None
    meta = getattr(match, "event_metadata", None)
    if meta is None and isinstance(match, dict):
        meta = match.get("event_metadata")

    nw: Optional[int] = None
    week: Optional[int] = None
    event_type: Optional[int] = None

    if ev is not None:
        if isinstance(ev, Mapping):
            nw = ev.get("normalized_week")
            week = ev.get("week")
            event_type = ev.get("event_type")
        else:
            nw = getattr(ev, "normalized_week", None)
            week = getattr(ev, "week", None)
            event_type = getattr(ev, "event_type", None)

    if isinstance(meta, Mapping):
        if nw is None:
            nw = meta.get("normalized_week")
        if week is None:
            week = meta.get("week")
        if event_type is None:
            event_type = meta.get("event_type")

    if nw is not None:
        norm_week = int(nw)
    elif week is not None:
        norm_week = int(week)
    elif event_type in (3, 4):
        norm_week = 8
    elif event_type == 100:
        norm_week = -1
    elif event_type == 99:
        norm_week = 10
    else:
        norm_week = 99

    stage_rank = 1 if event_type in (2, 4, 6) else 0
    return norm_week, stage_rank


def sort_event_block_reverse(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> List[Any]:
    """Sort matches by event-block interleave time with descending event_key tie-breaking."""
    match_list = list(matches)
    keys = event_block_sort_keys(match_list, events)
    order = sorted(
        range(len(match_list)),
        key=lambda i: (keys[i][0], keys[i][1], _rev_str(keys[i][2]), keys[i][3]),
    )
    return [match_list[i] for i in order]


def sort_untimed_round(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> List[Any]:
    """Sort matches round-by-round across simultaneous events in the same week and stage."""
    match_list = list(matches)
    lookup = _normalize_event_lookup(events)

    def _key(m: Any) -> Tuple[int, int, int, Tuple[int, int, int], str, str]:
        event_key, comp_level, set_number, match_number = get_match_identifiers(m)
        season = get_match_season(m, lookup or None)
        norm_week, stage_rank = _extract_week_and_stage(m, lookup)
        bkey = bracket_key(season, comp_level, set_number, match_number)
        mkey = str(
            getattr(m, "match_key", None)
            or getattr(m, "key", None)
            or (m.get("key") if isinstance(m, dict) else "")
            or ""
        )
        return (season, norm_week, stage_rank, bkey, event_key, mkey)

    return sorted(match_list, key=_key)


def sort_event_sequential(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
    descending: bool = False,
) -> List[Any]:
    """Sort matches event-by-event sequentially within each simultaneous week and stage."""
    match_list = list(matches)
    lookup = _normalize_event_lookup(events)

    def _key(m: Any) -> Tuple[Any, ...]:
        event_key, comp_level, set_number, match_number = get_match_identifiers(m)
        season = get_match_season(m, lookup or None)
        norm_week, stage_rank = _extract_week_and_stage(m, lookup)
        bkey = bracket_key(season, comp_level, set_number, match_number)
        mkey = str(
            getattr(m, "match_key", None)
            or getattr(m, "key", None)
            or (m.get("key") if isinstance(m, dict) else "")
            or ""
        )
        ev_order: Any = _rev_str(event_key) if descending else event_key
        return (season, norm_week, stage_rank, ev_order, bkey, mkey)

    return sorted(match_list, key=_key)


class StreamInvariantError(ValueError):
    """Raised when a replay stream violates an ordering invariant."""


def assert_stream_invariants(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
) -> None:
    """Check that a replay stream is safe to replay.

    Checks:
    1. Seasons form contiguous, non-decreasing blocks.
    2. Each event's matches appear in `bracket_key` order.
    3. No match key appears twice.

    Raises:
        StreamInvariantError: On the first violation found.
    """
    lookup = _normalize_event_lookup(events) or None
    seen_keys: set = set()
    last_season: Optional[int] = None
    last_bracket: Dict[str, Tuple[int, int, int]] = {}
    for pos, m in enumerate(matches):
        event_key, comp_level, set_number, match_number = get_match_identifiers(m)
        season = get_match_season(m, lookup)
        key = getattr(m, "key", None) or (m.get("key") if isinstance(m, dict) else None)
        if key is None:
            key = f"{event_key}_{comp_level}{set_number}m{match_number}"
        if key in seen_keys:
            raise StreamInvariantError(
                f"Duplicate match key '{key}' at stream position {pos}."
            )
        seen_keys.add(key)
        if last_season is not None and season < last_season:
            raise StreamInvariantError(
                f"Season order violated at position {pos}: {key} (season {season}) follows season {last_season}."
            )
        last_season = season
        bkey = bracket_key(season, comp_level, set_number, match_number)
        prev = last_bracket.get(event_key)
        if prev is not None and bkey <= prev:
            raise StreamInvariantError(
                f"Bracket order violated at position {pos}: {key} {bkey} follows {prev} in {event_key}."
            )
        last_bracket[event_key] = bkey


VALID_ORDER_MODES: Tuple[str, ...] = (
    "auto",
    "hybrid",
    "interleaved",
    "interleaved_rev",
    "untimed_round",
    "event_seq",
    "sequential",
    "event_seq_desc",
    "timed",
    "untimed",
)


def sort_replay_stream(
    matches: Sequence[Any],
    events: Optional[Union[Mapping[str, Any], Sequence[Any]]] = None,
    mode: str = "auto",
) -> List[Any]:
    """Sort a stream of matches for chronological replay.

    Args:
        matches: Sequence of TBAMatch, MatchContext, dict, or duck-typed match objects.
        events: Optional mapping or sequence of TBAEvent or event metadata dicts.
        mode: Ordering mode:
            - 'auto' (default), 'hybrid', and 'interleaved': two-level event-block order.
              Each event decides on its own whether it is timed. See `event_block_sort_keys`.
            - 'interleaved_rev': event-block order with descending event_key tie-breaking.
            - 'untimed_round': round-by-round interleaving across simultaneous events in the
              same week and stage while preserving `bracket_key`.
            - 'event_seq' and 'sequential': event-by-event sequential order within each
              simultaneous week and stage (ascending event_key).
            - 'event_seq_desc': event-by-event sequential order within each simultaneous
              week and stage (descending event_key).
            - 'timed': legacy global timestamp sort; raises ValueError if an untimed match exists.
            - 'untimed': legacy round-by-round progression key.

    Returns:
        Globally ordered list of matches ready for chronological two-phase replay.
    """
    if mode not in VALID_ORDER_MODES:
        raise ValueError(
            f"Invalid ordering mode: '{mode}'. Expected one of {VALID_ORDER_MODES}."
        )

    match_list = list(matches)
    if not match_list:
        return []

    if mode == "timed":
        return sort_timed_matches(match_list)
    if mode == "untimed":
        return sort_untimed_matches(match_list, events)
    if mode == "interleaved_rev":
        return sort_event_block_reverse(match_list, events)
    if mode == "untimed_round":
        return sort_untimed_round(match_list, events)
    if mode in ("event_seq", "sequential"):
        return sort_event_sequential(match_list, events, descending=False)
    if mode == "event_seq_desc":
        return sort_event_sequential(match_list, events, descending=True)
    return sort_event_block(match_list, events)


# Canonical alias
sort_matches = sort_replay_stream

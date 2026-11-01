"""The predictions_v2 pipeline: keeps each season's model state and match log current and
writes every changed event's EventPredictionsV2.

* ``advance``: apply the new and corrected results of some events of a season.
* ``rebuild``: replay a whole season in event-block order from the previous season's
  state (the backfill, and the recovery after a model version change).

A season's log holds every applied match in the order it was applied, with the prediction
made before its result was known. New results are appended, also when they arrive late. A
corrected, deleted or un-played result rewinds: the newest checkpoint at or before the
first changed entry is loaded, and the log from there is replayed with the current match
data. A season starts from the previous season's state at the time it starts.

Only tasks on the serial predictions-v2 queue call these functions, so each season has
one writer.
"""

import logging
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.predictions_v2 import store
from backend.common.helpers.predictions_v2.adapter import (
    build_stream,
    entry_kind,
    EntryKind,
    event_digest,
    stream_item,
    StreamItem,
    to_match_context,
)
from backend.common.helpers.predictions_v2.model.predictor import (
    HKFPredictor,
    MODEL_VERSION,
)
from backend.common.helpers.predictions_v2.ordering import event_block_order
from backend.common.helpers.predictions_v2.payload import match_prediction
from backend.common.manipulators.event_predictions_v2_manipulator import (
    EventPredictionsV2Manipulator,
)
from backend.common.models.event import Event
from backend.common.models.event_predictions_v2 import (
    EventPredictionsV2,
    MatchPredictionV2,
)
from backend.common.models.keys import EventKey, MatchKey, Year
from backend.common.models.match import Match
from backend.common.models.season_prediction_state import SeasonPredictionState
from backend.common.queries.event_query import EventListQuery
from backend.common.queries.match_query import EventMatchesQuery

FIRST_SEASON = 2002
# An event's within-event state is dropped once the stream reaches an event that ends
# this long after it.
PRUNE_AFTER = 7 * 86400
_DAY = 86400

# Season -> the last state this instance loaded or saved. It is used only while it is
# the stored generation, and it is evicted when a run fails.
_warm: Dict[Year, store.SeasonState] = {}


class NeedsRebuild(Exception):
    """The season cannot be advanced until it (or an earlier season) is rebuilt."""


def _clone(model: HKFPredictor) -> HKFPredictor:
    return HKFPredictor.decode_state(model.encode_state())


def _load(season: Year) -> Optional[store.SeasonState]:
    meta = SeasonPredictionState.key_for(season).get()
    cached = _warm.get(season)
    if meta is not None and cached is not None and cached.generation == meta.generation:
        return cached
    _warm.pop(season, None)
    state = store.load(season)
    if state is not None:
        _warm[season] = state
    return state


def _start_model(season: Year) -> HKFPredictor:
    """The model a new season starts from: a copy of the previous season's state."""
    if season <= FIRST_SEASON:
        return HKFPredictor()
    prev = _load(season - 1)
    if prev is None:
        raise NeedsRebuild(f"no current predictions_v2 state for {season - 1}")
    return _clone(prev.model)


class _Replay:
    """Applies stream entries to a season state and records the checkpoints it passes."""

    def __init__(self, state: store.SeasonState) -> None:
        self.state = state
        self.checkpoints: Dict[int, bytes] = {}
        self._ends: Dict[EventKey, Optional[int]] = {
            e.event_key: e.event_end for e in state.log
        }
        self._rolled: Optional[HKFPredictor] = None

    @property
    def season(self) -> Year:
        return self.state.season

    @property
    def model(self) -> HKFPredictor:
        return self.state.model

    def forecaster(self) -> HKFPredictor:
        """The model that predicts this season's matches. Until the season's first
        training entry rolls the state over, that is a rolled-over copy."""
        if self.model.season == self.season:
            return self.model
        if self._rolled is None:
            rolled = _clone(self.model)
            rolled.start_season(self.season)
            self._rolled = rolled
        return self._rolled

    def apply(self, item: StreamItem) -> None:
        index = len(self.state.log)
        if index % store.CHECKPOINT_EVERY == 0 and index not in self.state.checkpoints:
            self.checkpoints[index] = self.model.encode_state()
        end = item.slot.event_end + _DAY if item.slot.event_end is not None else None
        self._ends[item.context.event_key] = end
        if end is not None:
            done = []
            for ek in self.model.events:
                ek_end = self._ends.get(ek)
                if ek_end is not None and ek_end + PRUNE_AFTER < end:
                    done.append(ek)
            self.model.drop_events(done)
        if item.kind == EntryKind.TRAIN and self.model.season != self.season:
            self.model.start_season(self.season)
            self._rolled = None
        pred = self.forecaster().predict_match(item.context)
        self.state.log.append(
            store.LogEntry(
                match_key=item.context.match_key,
                event_key=item.context.event_key,
                kind=item.kind,
                fingerprint=item.fingerprint,
                event_end=end,
                prediction=match_prediction(pred, self.season, "pre_match"),
            )
        )
        if item.kind == EntryKind.TRAIN:
            self.model.update(item.context, item.outcome)


def _rewind(state: store.SeasonState, first: int) -> Tuple[_Replay, Set[EventKey]]:
    """Replay the log from the newest checkpoint at or before entry ``first`` with the
    current match data. Entries whose match is gone or unplayed are dropped."""
    start = max(i for i in state.checkpoints if i <= first)
    tail = state.log[start:]
    rewound = store.SeasonState(
        season=state.season,
        model=store.load_checkpoint(state, start),
        log=state.log[:start],
        checkpoints={i: s for i, s in state.checkpoints.items() if i <= start},
        generation=state.generation,
    )
    matches = ndb.get_multi([ndb.Key(Match, e.match_key) for e in tail])
    event_keys = sorted({e.event_key for e in tail})
    events = {
        k: ev
        for k, ev in zip(
            event_keys, ndb.get_multi([ndb.Key(Event, k) for k in event_keys])
        )
        if ev is not None
    }
    replay = _Replay(rewound)
    for match in matches:
        if match is None:
            continue
        event = events.get(match.event_key_name)
        item = stream_item(match, event) if event is not None else None
        if item is not None:
            replay.apply(item)
    logging.info(
        f"predictions_v2 {state.season}: rewound {len(tail)} entries from {start}"
    )
    return replay, set(event_keys)


def _project(replay: _Replay, event_keys: Iterable[EventKey]) -> None:
    """Write the predictions of the events: the logged pre-match prediction of every
    applied match, and a forecast from the current state for every unplayed match."""
    wanted = set(event_keys)
    logged: Dict[EventKey, Dict[MatchKey, MatchPredictionV2]] = defaultdict(dict)
    for entry in replay.state.log:
        if entry.event_key in wanted:
            logged[entry.event_key][entry.match_key] = entry.prediction
    for event_key in sorted(wanted):
        event = Event.get_by_id(event_key)
        kind = entry_kind(event) if event is not None else None
        if event is None or kind is None:
            continue
        matches = EventMatchesQuery(event_key).fetch()
        out: Dict[MatchKey, MatchPredictionV2] = {}
        for m in matches:
            if m.comp_level == CompLevel.PM:
                continue
            pred = logged[event_key].get(m.key_name)
            if pred is not None:
                out[m.key_name] = pred
            elif not m.has_been_played:
                ctx = to_match_context(m, event)
                if ctx.red_teams and ctx.blue_teams:
                    out[m.key_name] = match_prediction(
                        replay.forecaster().predict_match(ctx),
                        replay.season,
                        "forecast",
                    )
        EventPredictionsV2Manipulator.createOrUpdate(
            EventPredictionsV2(
                id=event_key,
                model_version=MODEL_VERSION,
                forecast_only=kind == EntryKind.FORECAST,
                matches=out,
                source_fingerprint=event_digest(matches),
            )
        )


def _save(replay: _Replay) -> store.SeasonState:
    saved = store.save(replay.state, replay.checkpoints)
    _warm[saved.season] = saved
    return saved


def needs_update(event: Event) -> bool:
    """Whether the event's matches changed since its predictions were written."""
    if entry_kind(event) is None:
        return False
    stored = EventPredictionsV2.get_by_id(event.key_name)
    if stored is None or stored.model_version != MODEL_VERSION:
        return True
    matches = EventMatchesQuery(event.key_name).fetch()
    return stored.source_fingerprint != event_digest(matches)


def advance(season: Year, events: Sequence[Event]) -> Set[EventKey]:
    """Apply the new and corrected results of the season's ``events`` and write the
    predictions of every event that changed. Returns the written event keys.

    Raises NeedsRebuild if the season has no current state to continue from.
    """
    try:
        return _advance(season, events)
    except Exception:
        _warm.pop(season, None)
        raise


def _advance(season: Year, events: Sequence[Event]) -> Set[EventKey]:
    state = _load(season)
    if state is None:
        if SeasonPredictionState.key_for(season).get() is not None:
            raise NeedsRebuild(f"predictions_v2 state for {season} is out of date")
        state = store.SeasonState(season=season, model=_start_model(season))
    index = {e.match_key: i for i, e in enumerate(state.log)}
    logged_by_event: Dict[EventKey, List[int]] = defaultdict(list)
    for i, e in enumerate(state.log):
        logged_by_event[e.event_key].append(i)

    fixes: List[int] = []
    new: List[StreamItem] = []
    touched: Set[EventKey] = set()
    for event in events:
        if event.year != season or entry_kind(event) is None:
            continue
        matches = EventMatchesQuery(event.key_name).fetch()
        if needs_update(event):
            touched.add(event.key_name)
        current = {m.key_name for m in matches}
        for m in matches:
            i = index.get(m.key_name)
            item = stream_item(m, event)
            if item is None:
                if i is not None:
                    fixes.append(i)  # un-played or became a practice match
            elif i is None:
                new.append(item)
            else:
                entry = state.log[i]
                if entry.kind != item.kind or (
                    item.kind == EntryKind.TRAIN
                    and entry.fingerprint != item.fingerprint
                ):
                    fixes.append(i)
        fixes += [
            i
            for i in logged_by_event[event.key_name]
            if state.log[i].match_key not in current
        ]

    if fixes:
        replay, rewound = _rewind(state, min(fixes))
        touched |= rewound
    else:
        replay = _Replay(
            store.SeasonState(
                season=state.season,
                model=state.model,
                log=list(state.log),
                checkpoints=dict(state.checkpoints),
                generation=state.generation,
            )
        )
    for i in event_block_order([it.slot for it in new]):
        replay.apply(new[i])
        touched.add(new[i].context.event_key)
    if fixes or new:
        _save(replay)
    _project(replay, touched)
    return touched


def rebuild(season: Year) -> None:
    """Replay the whole season in event-block order and write all its predictions."""
    try:
        _rebuild(season)
    except Exception:
        _warm.pop(season, None)
        raise


def _rebuild(season: Year) -> None:
    meta = SeasonPredictionState.key_for(season).get()
    state = store.SeasonState(
        season=season,
        model=_start_model(season),
        generation=meta.generation if meta is not None else -1,
    )
    events = {e.key_name: e for e in EventListQuery(year=season).fetch()}
    matches = [m for ek in events for m in EventMatchesQuery(ek).fetch()]
    replay = _Replay(state)
    for item in build_stream(events, matches):
        replay.apply(item)
    _save(replay)
    _project(replay, [k for k, e in events.items() if entry_kind(e) is not None])
    logging.info(f"predictions_v2 {season}: rebuilt {len(replay.state.log)} entries")

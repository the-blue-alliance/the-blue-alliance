"""Persistence of a season's predictions_v2 state.

A season has a model state, an append-only match log and checkpoints (the model state
before log entry i, every ``CHECKPOINT_EVERY`` entries). The blobs live in Cloud Storage
and ``SeasonPredictionState`` points at them. Every blob is double-buffered: a save
writes the slot the entity does not point at, then updates the entity, so a failed save
leaves the previous state intact and storage stays bounded.
"""

import gzip
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from backend.common import storage
from backend.common.helpers.predictions_v2.adapter import EntryKind
from backend.common.helpers.predictions_v2.model.config import DEFAULT_CONFIG
from backend.common.helpers.predictions_v2.model.predictor import (
    HKFPredictor,
    model_fingerprint,
)
from backend.common.helpers.predictions_v2.model.state import StateVersionError
from backend.common.models.event_predictions_v2 import MatchPredictionV2
from backend.common.models.keys import EventKey, MatchKey, Year
from backend.common.models.season_prediction_state import SeasonPredictionState

STORAGE_PREFIX = "predictions_v2"
CHECKPOINT_EVERY = 1000


@dataclass(frozen=True)
class LogEntry:
    match_key: MatchKey
    event_key: EventKey
    kind: EntryKind
    # outcome_fingerprint of the result the model learned (train entries).
    fingerprint: str
    # Unix seconds of the end of the event's last day (for pruning event state).
    event_end: Optional[int]
    # The prediction made before the result was known.
    prediction: MatchPredictionV2

    def to_json(self) -> Dict[str, Any]:
        return {
            "match_key": self.match_key,
            "event_key": self.event_key,
            "kind": self.kind.value,
            "fingerprint": self.fingerprint,
            "event_end": self.event_end,
            "prediction": self.prediction,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Any]) -> "LogEntry":
        return cls(
            match_key=data["match_key"],
            event_key=data["event_key"],
            kind=EntryKind(data["kind"]),
            fingerprint=data["fingerprint"],
            event_end=data["event_end"],
            prediction=data["prediction"],
        )


@dataclass
class SeasonState:
    season: Year
    model: HKFPredictor
    log: List[LogEntry] = field(default_factory=list)
    # Log index -> slot of the checkpoint before that entry.
    checkpoints: Dict[int, int] = field(default_factory=dict)
    # Generation of the stored state this was loaded from (-1: never saved).
    generation: int = -1


def _path(season: Year, name: str, slot: int) -> str:
    return f"{STORAGE_PREFIX}/{season}/{name}.slot{slot}"


def _checkpoint_name(index: int) -> str:
    return f"checkpoint_{index:06d}.npz"


def _encode_log(log: List[LogEntry]) -> bytes:
    lines = "".join(json.dumps(e.to_json(), separators=(",", ":")) + "\n" for e in log)
    return gzip.compress(lines.encode(), mtime=0)


def _decode_log(blob: bytes) -> List[LogEntry]:
    lines = gzip.decompress(blob).decode().splitlines()
    return [LogEntry.from_json(json.loads(line)) for line in lines if line]


def _read_bytes(path: str) -> bytes:
    blob = storage.read(path)
    if blob is None:
        raise FileNotFoundError(path)
    return blob if isinstance(blob, bytes) else blob.encode()


def load(season: Year) -> Optional[SeasonState]:
    """The stored state of a season, or None if there is none or it was written by
    another model version."""
    meta = SeasonPredictionState.key_for(season).get()
    if meta is None or meta.model_fingerprint != model_fingerprint(DEFAULT_CONFIG):
        return None
    slot = meta.generation % 2
    try:
        model = HKFPredictor.decode_state(_read_bytes(_path(season, "state.npz", slot)))
    except StateVersionError:
        return None
    log = _decode_log(_read_bytes(_path(season, "log.jsonl.gz", slot)))
    if len(log) != meta.log_length:
        raise ValueError(
            f"{season}: log has {len(log)} entries, expected {meta.log_length}"
        )
    return SeasonState(
        season=season,
        model=model,
        log=log,
        checkpoints={int(k): v for k, v in (meta.checkpoints or {}).items()},
        generation=meta.generation,
    )


def load_checkpoint(state: SeasonState, index: int) -> HKFPredictor:
    slot = state.checkpoints[index]
    return HKFPredictor.decode_state(
        _read_bytes(_path(state.season, _checkpoint_name(index), slot))
    )


def save(
    state: SeasonState, new_checkpoints: Optional[Mapping[int, bytes]] = None
) -> SeasonState:
    """Store the state, log and new checkpoints (encoded model states). Checkpoints past
    the end of the log are dropped. Returns the state with its new generation."""
    generation = state.generation + 1
    slot = generation % 2
    season = state.season
    storage.write(
        _path(season, "state.npz", slot),
        state.model.encode_state(),
        content_type="application/octet-stream",
    )
    storage.write(
        _path(season, "log.jsonl.gz", slot),
        _encode_log(state.log),
        content_type="application/gzip",
    )
    checkpoints = {i: s for i, s in state.checkpoints.items() if i <= len(state.log)}
    for index, blob in (new_checkpoints or {}).items():
        ck_slot = 1 - checkpoints[index] if index in checkpoints else 0
        storage.write(
            _path(season, _checkpoint_name(index), ck_slot),
            blob,
            content_type="application/octet-stream",
        )
        checkpoints[index] = ck_slot
    SeasonPredictionState(
        id=str(season),
        season=season,
        model_fingerprint=model_fingerprint(state.model.cfg),
        generation=generation,
        log_length=len(state.log),
        checkpoints={str(i): s for i, s in sorted(checkpoints.items())},
    ).put()
    return SeasonState(
        season=season,
        model=state.model,
        log=list(state.log),
        checkpoints=checkpoints,
        generation=generation,
    )

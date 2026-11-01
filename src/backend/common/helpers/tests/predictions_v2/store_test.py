from typing import List

import pytest

from backend.common import storage
from backend.common.helpers.predictions_v2 import store
from backend.common.helpers.predictions_v2.adapter import EntryKind
from backend.common.helpers.predictions_v2.model.predictor import HKFPredictor
from backend.common.helpers.predictions_v2.payload import match_prediction
from backend.common.helpers.tests.predictions_v2.model.golden import (
    GoldenMatch,
    load_golden,
)
from backend.common.models.season_prediction_state import SeasonPredictionState


@pytest.fixture(autouse=True)
def auto_use_gcs_stub(gcs_stub) -> None:
    pass


def _run(n: int) -> store.SeasonState:
    matches: List[GoldenMatch] = [m for m in load_golden() if m.year == 2016][:n]
    model = HKFPredictor()
    model.start_season(2016)
    log = []
    for m in matches:
        pred = model.predict_match(m.context)
        log.append(
            store.LogEntry(
                match_key=m.context.match_key,
                event_key=m.context.event_key,
                kind=EntryKind.TRAIN,
                fingerprint=f"fp-{m.context.match_key}",
                event_end=None,
                prediction=match_prediction(pred, 2016, "pre_match"),
            )
        )
        model.update(m.context, m.outcome)
    return store.SeasonState(season=2016, model=model, log=log)


def test_load_without_a_stored_state() -> None:
    assert store.load(2016) is None


def test_save_and_load_round_trip() -> None:
    state = _run(30)
    saved = store.save(state, {0: HKFPredictor().encode_state()})
    assert saved.generation == 0

    loaded = store.load(2016)
    assert loaded is not None
    assert loaded.generation == 0
    assert loaded.log == state.log
    assert loaded.checkpoints == {0: 0}
    assert loaded.model.encode_state() and loaded.model.n == state.model.n
    assert store.load_checkpoint(loaded, 0).n == 0

    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None and meta.log_length == 30


def test_saves_alternate_slots_and_checkpoints_past_the_log_are_dropped() -> None:
    state = store.save(
        _run(30), {10: HKFPredictor().encode_state(), 20: HKFPredictor().encode_state()}
    )
    state = store.save(state, {10: HKFPredictor().encode_state()})
    assert state.generation == 1
    assert state.checkpoints == {10: 1, 20: 0}
    assert storage.read("predictions_v2/2016/state.npz.slot0") is not None
    assert storage.read("predictions_v2/2016/state.npz.slot1") is not None

    # A rewind truncates the log: later checkpoints no longer apply.
    state.log = state.log[:15]
    state = store.save(state)
    assert state.checkpoints == {10: 1}
    loaded = store.load(2016)
    assert loaded is not None and len(loaded.log) == 15


def test_failed_save_keeps_the_previous_state(monkeypatch: pytest.MonkeyPatch) -> None:
    first = store.save(_run(10))
    bigger = _run(20)
    bigger.generation = first.generation

    def fail(*args, **kwargs) -> None:
        raise IOError("storage unavailable")

    monkeypatch.setattr(storage, "write", fail)
    with pytest.raises(IOError):
        store.save(bigger)
    monkeypatch.undo()

    loaded = store.load(2016)
    assert loaded is not None
    assert loaded.generation == 0
    assert len(loaded.log) == 10


def test_state_of_another_model_version_is_not_loaded() -> None:
    store.save(_run(5))
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None
    meta.model_fingerprint = "old"
    meta.put()
    assert store.load(2016) is None

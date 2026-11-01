import json
from typing import Dict, List

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2 import pipeline, store
from backend.common.helpers.predictions_v2.adapter import build_stream
from backend.common.helpers.predictions_v2.backtest import replay
from backend.common.helpers.predictions_v2.model import state as state_codec
from backend.common.helpers.predictions_v2.model.predictor import (
    HKFPredictor,
    MODEL_VERSION,
)
from backend.common.helpers.predictions_v2.payload import match_prediction
from backend.common.helpers.tests.predictions_v2.api_fixture import store_api_fixture
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.event import Event
from backend.common.models.event_predictions_v2 import (
    EventPredictionsV2,
    MatchPredictionV2,
)
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.common.models.season_prediction_state import SeasonPredictionState


@pytest.fixture(autouse=True)
def setup(gcs_stub, taskqueue_stub, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "FIRST_SEASON", 2016)
    monkeypatch.setattr(store, "CHECKPOINT_EVERY", 50)
    pipeline._warm.clear()


def _flush() -> None:
    """Clear the cached queries, as the cache clearing of a write does."""
    ndb.delete_multi(CachedQueryResult.query().fetch(keys_only=True))


def _events(year: int) -> List[Event]:
    return [e for e in Event.query(Event.year == year).fetch()]


def _set_score(match_key: str, red: int, blue: int) -> None:
    """Edit a result the way the site does: through the manipulator (cache clearing)."""
    m = none_throws(Match.get_by_id(match_key))
    alliances = m.alliances
    alliances[AllianceColor.RED]["score"] = red
    alliances[AllianceColor.BLUE]["score"] = blue
    edited = Match(
        id=match_key,
        event=m.event,
        year=m.year,
        comp_level=m.comp_level,
        set_number=m.set_number,
        match_number=m.match_number,
        team_key_names=m.team_key_names,
        alliances_json=json.dumps(alliances),
        score_breakdown_json=m.score_breakdown_json,
    )
    MatchManipulator.createOrUpdate(edited)
    _flush()


def _expected(events: Dict, matches: List[Match]) -> Dict[MatchKey, MatchPredictionV2]:
    """Pre-match predictions of a clean replay of the matches in event-block order."""
    out: Dict[MatchKey, MatchPredictionV2] = {}
    replay(
        build_stream(events, matches),
        on_prediction=lambda it, pred: out.__setitem__(
            it.context.match_key, match_prediction(pred, it.year, "pre_match")
        ),
    )
    return out


def _state_tree(model: HKFPredictor) -> str:
    enc = state_codec._Encoder()
    tree = json.dumps(enc.enc(model), sort_keys=True)
    return tree + "".join(a.tobytes().hex() for a in enc.arrays)


def _served(event_key: str) -> Dict[MatchKey, MatchPredictionV2]:
    p = EventPredictionsV2.get_by_id(event_key)
    assert p is not None
    return p.matches


def test_advance_applies_results_and_writes_predictions() -> None:
    events, matches = store_api_fixture({2016})
    written = pipeline.advance(2016, _events(2016))

    assert written == set(events)
    expected = _expected(events, matches)
    for ek in events:
        served = _served(ek)
        assert served == {k: v for k, v in expected.items() if k.startswith(ek)}
        stored = EventPredictionsV2.get_by_id(ek)
        assert stored is not None and stored.model_version == MODEL_VERSION
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None and meta.generation == 0 and meta.log_length == len(matches)
    # Checkpoints every 50 entries, starting before the first entry.
    assert set(int(k) for k in meta.checkpoints) == set(range(0, len(matches), 50))


def test_advance_without_changes_does_nothing() -> None:
    store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    assert pipeline.advance(2016, _events(2016)) == set()
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None and meta.generation == 0


def test_late_results_are_appended_without_rewind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, matches = store_api_fixture({2016})
    late = sorted(m.key_name for m in matches if m.comp_level != "qm")[:5]
    scores = {
        k: (
            m.alliances[AllianceColor.RED]["score"],
            m.alliances[AllianceColor.BLUE]["score"],
        )
        for k, m in ((k, none_throws(Match.get_by_id(k))) for k in late)
    }
    for k in late:
        _set_score(k, -1, -1)
    pipeline.advance(2016, _events(2016))
    first = store.load(2016)
    assert first is not None

    def no_rewind(*args, **kwargs):
        raise AssertionError("rewound")

    monkeypatch.setattr(pipeline, "_rewind", no_rewind)
    for k in late:
        _set_score(k, *scores[k])
    pipeline.advance(2016, _events(2016))

    second = store.load(2016)
    assert second is not None
    # The earlier entries are untouched; the late results follow them.
    assert second.log[: len(first.log)] == first.log
    assert {e.match_key for e in second.log[len(first.log) :]} == set(late)
    assert second.generation == first.generation + 1


def test_correction_rewinds_and_reprojects() -> None:
    events, matches = store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    before = store.load(2016)
    assert before is not None
    i = 80
    target = before.log[i].match_key
    old = none_throws(Match.get_by_id(target)).alliances
    _set_score(
        target, old[AllianceColor.RED]["score"] + 40, old[AllianceColor.BLUE]["score"]
    )

    written = pipeline.advance(2016, _events(2016))

    after = store.load(2016)
    assert after is not None
    assert [e.match_key for e in after.log] == [e.match_key for e in before.log]
    # Entries before the correction keep their predictions; the corrected match keeps its
    # pre-match prediction; later predictions change.
    assert after.log[: i + 1] == [
        e if j != i else after.log[i] for j, e in enumerate(before.log[: i + 1])
    ]
    assert after.log[i].prediction == before.log[i].prediction
    assert after.log[i].fingerprint != before.log[i].fingerprint
    assert any(
        a.prediction != b.prediction
        for a, b in zip(after.log[i + 1 :], before.log[i + 1 :])
    )
    assert target.split("_")[0] in written
    # The result equals a clean replay of the corrected data.
    current = Match.query(Match.year == 2016).fetch()
    expected = _expected(events, current)
    assert {e.match_key: e.prediction for e in after.log} == expected


def test_unplayed_result_leaves_the_log_and_gets_a_forecast() -> None:
    store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    before = store.load(2016)
    assert before is not None
    target = before.log[40].match_key
    _set_score(target, -1, -1)

    pipeline.advance(2016, _events(2016))

    after = store.load(2016)
    assert after is not None
    assert target not in {e.match_key for e in after.log}
    assert len(after.log) == len(before.log) - 1
    assert _served(target.split("_")[0])[target]["kind"] == "forecast"


def test_forecast_only_event_is_predicted_but_not_learned() -> None:
    events, _ = store_api_fixture({2016})
    offseason = sorted(events)[0]
    e = none_throws(Event.get_by_id(offseason))
    e.event_type_enum = EventType.OFFSEASON
    EventManipulator.createOrUpdate(e)
    _flush()

    pipeline.advance(2016, [none_throws(Event.get_by_id(offseason))])

    state = store.load(2016)
    assert state is not None and state.log
    assert all(entry.kind.value == "forecast" for entry in state.log)
    # Nothing was learned: the model has not even rolled over into 2016.
    assert state.model.n == 0
    stored = EventPredictionsV2.get_by_id(offseason)
    assert stored is not None and stored.forecast_only


def test_schedule_change_reprojects_without_saving() -> None:
    events, matches = store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    ek = sorted(events)[1]
    template = next(
        m for m in matches if m.event_key_name == ek and m.comp_level == "qm"
    )
    new = Match(
        id=f"{ek}_qm999",
        event=ndb.Key(Event, ek),
        year=2016,
        comp_level="qm",
        set_number=1,
        match_number=999,
        team_key_names=template.team_key_names,
        alliances_json=json.dumps(
            {
                c: {
                    "teams": template.alliances[c]["teams"],
                    "score": -1,
                    "surrogates": [],
                    "dqs": [],
                }
                for c in (AllianceColor.RED, AllianceColor.BLUE)
            }
        ),
    )
    MatchManipulator.createOrUpdate(new)
    _flush()

    written = pipeline.advance(2016, _events(2016))

    assert written == {ek}
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None and meta.generation == 0
    assert _served(ek)[f"{ek}_qm999"]["kind"] == "forecast"


def test_failed_run_evicts_the_warm_state_and_the_retry_persists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, matches = store_api_fixture({2016})
    calls = []
    real_save = store.save

    def flaky_save(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise IOError("storage unavailable")
        return real_save(*args, **kwargs)

    monkeypatch.setattr(store, "save", flaky_save)
    with pytest.raises(IOError):
        pipeline.advance(2016, _events(2016))
    assert 2016 not in pipeline._warm
    assert SeasonPredictionState.key_for(2016).get() is None

    pipeline.advance(2016, _events(2016))
    state = store.load(2016)
    assert state is not None
    assert {e.match_key: e.prediction for e in state.log} == _expected(events, matches)


def test_stale_warm_state_is_reloaded() -> None:
    store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    cached = pipeline._warm[2016]
    cached.generation = -5  # another instance saved since
    assert pipeline._load(2016) is not cached


def test_new_season_starts_from_the_previous_season() -> None:
    store_api_fixture({2016, 2017})
    pipeline.advance(2016, _events(2016))
    end_of_2016 = store.load(2016)
    assert end_of_2016 is not None

    pipeline.advance(2017, _events(2017))

    state_2017 = store.load(2017)
    assert state_2017 is not None and state_2017.model.season == 2017
    # The 2017 log starts from the 2016 state as it was when 2017 began.
    start = store.load_checkpoint(state_2017, 0)
    assert _state_tree(start) == _state_tree(end_of_2016.model)
    with pytest.raises(pipeline.NeedsRebuild):
        pipeline.advance(2019, _events(2017))


def test_state_of_another_model_version_needs_a_rebuild() -> None:
    store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None
    meta.model_fingerprint = "old"
    meta.put()
    pipeline._warm.clear()
    with pytest.raises(pipeline.NeedsRebuild):
        pipeline.advance(2016, _events(2016))


def test_rebuild_replays_the_season_in_event_block_order() -> None:
    events, matches = store_api_fixture({2016})
    pipeline.rebuild(2016)
    state = store.load(2016)
    assert state is not None
    assert {e.match_key: e.prediction for e in state.log} == _expected(events, matches)
    assert [e.match_key for e in state.log] == [
        it.context.match_key for it in build_stream(events, matches)
    ]
    # A rebuild over an existing state writes the other slot.
    pipeline.rebuild(2016)
    meta = SeasonPredictionState.key_for(2016).get()
    assert meta is not None and meta.generation == 1


def test_finished_events_are_pruned() -> None:
    events, _ = store_api_fixture({2016})
    pipeline.advance(2016, _events(2016))
    state = store.load(2016)
    assert state is not None
    ends = {e.event_key: none_throws(e.event_end) for e in state.log}
    last = state.log[-1].event_key
    assert last in state.model.events
    # Only events that ended within PRUNE_AFTER of the last one keep their state.
    assert len(events) == 2
    for ek in events:
        kept = ends[ek] + pipeline.PRUNE_AFTER >= ends[last]
        assert (ek in state.model.events) == kept

import dataclasses
import json
import math
from typing import Any, List, Tuple

import numpy as np
import pytest

from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2.model import state
from backend.common.helpers.predictions_v2.model.config import HKFConfig
from backend.common.helpers.predictions_v2.model.predictor import HKFPredictor
from backend.common.helpers.tests.predictions_v2.model.golden import (
    GoldenMatch,
    load_golden,
    replay,
    summarize,
    Summary,
)


@pytest.fixture(scope="module")
def golden() -> List[GoldenMatch]:
    return load_golden()


def _assert_close(actual: Any, expected: Any, where: str) -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict), where
        assert set(actual) == set(expected), where
        for k in expected:
            _assert_close(actual[k], expected[k], f"{where}.{k}")
    elif isinstance(expected, float) and not isinstance(actual, bool):
        assert math.isclose(
            actual, expected, rel_tol=1e-9, abs_tol=1e-12
        ), f"{where}: {actual} != {expected}"
    else:
        assert actual == expected, where


def _snapshot(model: HKFPredictor) -> Tuple[str, List[np.ndarray]]:
    enc = state._Encoder()
    tree = json.dumps(enc.enc(model), sort_keys=True)
    return tree, enc.arrays


def _same_snapshot(
    a: Tuple[str, List[np.ndarray]], b: Tuple[str, List[np.ndarray]]
) -> bool:
    return a[0] == b[0] and all(
        x.shape == y.shape and np.array_equal(x, y, equal_nan=True)
        for x, y in zip(a[1], b[1])
    )


def test_golden_stream(golden: List[GoldenMatch]) -> None:
    got = replay(HKFPredictor(), golden)
    for m, summary in zip(golden, got):
        _assert_close(summary, m.expected, m.context.match_key)


def test_state_round_trip_continues_identically(golden: List[GoldenMatch]) -> None:
    matches = [m for m in golden if m.year <= 2018]
    expected = replay(HKFPredictor(), matches)

    model = HKFPredictor()
    got: List[Summary] = []
    for i, m in enumerate(matches):
        if i % 60 == 0 or model.season != m.year:
            model = HKFPredictor.decode_state(model.encode_state())
        if model.season != m.year:
            model.start_season(m.year)
        got.append(summarize(model.predict_match(m.context), m.outcome))
        model.update(m.context, m.outcome)
    assert got == expected


def test_predict_match_does_not_change_state(golden: List[GoldenMatch]) -> None:
    model = HKFPredictor()
    for i, m in enumerate(golden[:400]):
        if model.season != m.year:
            model.start_season(m.year)
        if i % 40 == 0:
            before = _snapshot(model)
            model.predict_match(m.context)
            # A forecast-only (offseason) match of the same teams.
            model.predict_match(
                dataclasses.replace(
                    m.context,
                    event_key=f"{m.year}offseason",
                    event_type=EventType.OFFSEASON,
                )
            )
            assert _same_snapshot(before, _snapshot(model)), m.context.match_key
        model.update(m.context, m.outcome)


def test_dropping_finished_events_keeps_outputs(golden: List[GoldenMatch]) -> None:
    matches = [m for m in golden if m.year <= 2019]
    last = {m.context.event_key: i for i, m in enumerate(matches)}
    expected = replay(HKFPredictor(), matches)

    model = HKFPredictor()
    got: List[Summary] = []
    for i, m in enumerate(matches):
        if model.season != m.year:
            model.start_season(m.year)
        got.append(summarize(model.predict_match(m.context), m.outcome))
        model.update(m.context, m.outcome)
        model.drop_events([ek for ek, j in last.items() if j == i])
    assert got == expected
    assert model.events == {}
    assert model.ecount == {}
    assert model.po_res == {}


def test_state_of_another_config_is_rejected(golden: List[GoldenMatch]) -> None:
    model = HKFPredictor()
    replay(model, golden[:50])
    blob = model.encode_state()
    with pytest.raises(state.StateVersionError):
        HKFPredictor.decode_state(blob, HKFConfig(pcg_reg=1.0))


def test_new_season_carries_team_strength(golden: List[GoldenMatch]) -> None:
    model = HKFPredictor()
    replay(model, [m for m in golden if m.year == 2016])
    team = golden[0].context.red_teams[0]

    model.start_season(2017)
    # The season-end total (after the cross-event blend and de-drift) is recorded and
    # carried into the new season with the rho decay.
    season_end_total = float(model.teams[team][0].sum())
    assert model.hist[team] == [(2016, season_end_total)]
    h = model._hyper()
    carried = model._prior_z_scalar(team, h)
    assert math.isclose(carried, model.cfg.rho * season_end_total)
    assert carried != model._prior_z_scalar("frc999999", h)

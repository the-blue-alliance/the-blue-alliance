import math

import numpy as np

from backend.common.helpers.predictions_v2.model.rulebook import ScoreComponent
from backend.common.helpers.predictions_v2.model.structure import (
    ComponentModel,
    MIN_READY,
    ScoreStructure,
)


def _trained_model() -> ComponentModel:
    cm = ComponentModel(
        [
            ScoreComponent("rotorPoints", 40),
            ScoreComponent("bonus", 20, playoff_only=True),
        ]
    )
    rng = np.random.default_rng(0)
    for i in range(MIN_READY):
        bd = {"rotorPoints": 40 * int(rng.integers(0, 4)), "bonus": 0}
        cm.update(
            ["frc1", "frc2", "frc3"] if i % 2 else ["frc4", "frc5", "frc6"], False, bd
        )
    return cm


def test_component_model_is_ready_after_enough_breakdowns() -> None:
    cm = ComponentModel([ScoreComponent("rotorPoints", 40)])
    for _ in range(MIN_READY - 1):
        cm.update(["frc1", "frc2", "frc3"], False, {"rotorPoints": 80})
    assert not cm.ready()
    cm.update(["frc1", "frc2", "frc3"], False, {"rotorPoints": 80})
    assert cm.ready()


def test_breakdowns_without_the_field_are_skipped() -> None:
    cm = ComponentModel([ScoreComponent("rotorPoints", 40)])
    cm.update(["frc1"], False, {"other": 1})
    cm.update(["frc1"], False, None)
    cm.update(["frc1"], False, {"rotorPoints": 30})  # not a multiple of the step
    assert cm.n_obs == 1
    assert cm.comps[0].gn == 0


def test_forecast_keeps_the_mean_and_the_score_steps() -> None:
    cm = _trained_model()
    pmf = cm.forecast(["frc1", "frc2", "frc3"], False, 60.0, 30.0)
    assert pmf is not None
    k = np.arange(len(pmf))
    assert abs(float(pmf @ k) - 60.0) < 1e-3
    assert float(pmf[k % 40 != 0].sum()) < 1e-9


def test_structure_without_a_rulebook_table_is_off() -> None:
    s = ScoreStructure(eta=0.5, alpha=1e-3, lam=0.25)
    s.start_season(2014)
    assert s.cm is None
    pe = np.full(10, 0.1)
    assert s.arms(pe, ["frc1"], False, 4.5, 2.0) is None
    np.testing.assert_array_equal(s.mix(pe, None), pe)


def test_mix_keeps_the_base_mean_and_learn_moves_the_weights() -> None:
    s = ScoreStructure(eta=0.5, alpha=1e-3, lam=0.25)
    pe = np.full(20, 0.05)
    pb = np.zeros(20)
    pb[::5] = 0.25
    mixed = s.mix(pe, pb)
    k = np.arange(20)
    assert abs(float(mixed @ k) - float(pe @ k)) < 1e-6

    s.learn([(pe, pb, 10), (pe, pb, 15)])  # the stepped arm fits better
    w_stepped = float(s.w[1])
    assert w_stepped > 0.5
    # A new season shrinks the weights toward uniform.
    s.start_season(2017)
    assert math.isclose(float(s.w[1]), (1 - 0.25) * w_stepped + 0.25 / 2)

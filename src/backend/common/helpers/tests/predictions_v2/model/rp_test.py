import numpy as np

from backend.common.helpers.predictions_v2.model.rp import BonusModel, OnlineLogit


def test_online_logit_learns_toward_the_label() -> None:
    m = OnlineLogit(2, [1.0, 1.0], q=0.0)
    x = np.array([1.0, 0.5])
    assert m.prob(x) == 0.5
    for _ in range(20):
        m.update(x, 1.0)
    assert m.prob(x) > 0.8
    assert m.prob(-x) < 0.2


def test_bonus_model_defaults_to_one_half_for_an_unseen_key() -> None:
    b = BonusModel([4.0] * 4, q=1e-4)
    x = np.array([1.0, 0.2, 0.1, -0.3])
    assert b.probs(["rp_1"], x) == {"rp_1": 0.5}
    b.update({"rp_1": 1}, x)
    assert b.probs(["rp_1"], x)["rp_1"] > 0.5
    b.reset()
    assert b.models == {}

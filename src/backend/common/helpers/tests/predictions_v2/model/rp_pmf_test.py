import math

import numpy as np
import pytest

from backend.common.helpers.predictions_v2.model.rp_pmf import rp_values, RPJoint


@pytest.mark.parametrize("p", [0.1, 0.5, 0.83])
def test_pmf_keeps_the_marginals(p: float) -> None:
    j = RPJoint(rho_prior=0.3, rho_prior_sd=0.2)
    bonus = {"rp_1": 0.7, "rp_2": 0.2, "rp_3": 0.4}
    wv, tv = rp_values(2025)
    pmf = j.pmf(p, bonus, wv, tv)
    pw, pt, pl = j.outcome_probs(p)
    assert math.isclose(pw + pt + pl, 1.0)
    assert math.isclose(float(pmf.sum()), 1.0)
    expected = wv * pw + tv * pt + sum(bonus.values())
    assert math.isclose(float(pmf @ np.arange(len(pmf))), expected, abs_tol=1e-6)


def test_rp_values() -> None:
    assert rp_values(2024) == (2, 1)
    assert rp_values(2025) == (3, 1)


def test_bonus_correlation_is_learned() -> None:
    j = RPJoint(rho_prior=0.3, rho_prior_sd=0.2)
    prior = j.rho("rp_1")
    for _ in range(200):
        # The bonus comes with wins only: a strong positive correlation.
        j.update_bonus(0.5, {"rp_1": 0.5}, "W", {"rp_1": 1})
        j.update_bonus(0.5, {"rp_1": 0.5}, "L", {"rp_1": 0})
    assert j.rho("rp_1") > prior
    j.start_season()
    assert math.isclose(j.rho("rp_1"), prior)
    assert RPJoint.median(np.array([0.2, 0.2, 0.6])) == 2.0

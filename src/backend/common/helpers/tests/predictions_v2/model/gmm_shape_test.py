import numpy as np

from backend.common.helpers.predictions_v2.model.gmm_shape import (
    BucketGmmShape,
    GmmShape,
)


def _shape() -> GmmShape:
    return GmmShape(B=8.0, K=5, kn=500.0, kp=500.0, sdscale=1.0)


def test_prior_shape_is_a_centered_cdf() -> None:
    g = _shape()
    z = np.linspace(-8.0, 8.0, 161)
    cdf = g.cdf(z)
    assert np.all(np.diff(cdf) >= 0.0)
    assert cdf[0] < 1e-9 and cdf[-1] > 1.0 - 1e-9
    assert abs(float(g.cdf(np.array([0.0]))[0]) - 0.5) < 1e-3


def test_residuals_change_the_shape_and_roll_pools_them() -> None:
    g = _shape()
    before = g.cdf(np.array([1.0]))[0]
    for _ in range(500):
        g.add(2.0)  # a heavy right tail
        g.add(-0.4)
    after = g.cdf(np.array([1.0]))[0]
    assert after != before
    assert g.cur_n == 1000.0
    g.roll()
    assert g.cur_n == 0.0 and g.pool_n == 1000.0


def test_bucket_shape_starts_at_the_global_shape() -> None:
    g = _shape()
    for _ in range(300):
        g.add(1.5)
    b = BucketGmmShape(g, kg=2000.0, B=8.0, K=5, kp=500.0, sdscale=1.0)
    z = np.linspace(-3.0, 3.0, 13)
    np.testing.assert_allclose(b.cdf(z), g.cdf(z), atol=1e-2)

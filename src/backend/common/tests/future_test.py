import pytest

from backend.common.futures import FailedFuture, InstantFuture, TypedFuture


def test_instant_future() -> None:
    f = InstantFuture(42)
    assert f.done() is True
    assert f.get_result() == 42


def test_failed_future() -> None:
    e = Exception("welp")
    f: TypedFuture[int] = FailedFuture(e)
    assert f.done() is True
    assert f.get_exception() == e
    with pytest.raises(Exception):
        f.get_result()
    with pytest.raises(Exception):
        f.check_success()

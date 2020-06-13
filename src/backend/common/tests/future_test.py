import pytest
from backend.common.futures import TypedFuture, InstantFuture, FailedFuture


def test_instant_future() -> None:
    f: TypedFuture[int] = InstantFuture(42)
    assert f.running() is False
    assert f.done() is True
    assert f.result() == 42


def test_failed_future() -> None:
    e = Exception("welp")
    f: TypedFuture[int] = FailedFuture(e)
    assert f.running() is False
    assert f.done() is True
    assert f.exception() == e
    with pytest.raises(Exception):
        f.result()
    with pytest.raises(Exception):
        f.check_success()

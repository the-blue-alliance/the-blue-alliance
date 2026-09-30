import contextvars
from types import SimpleNamespace
from typing import Any, List

from _pytest.monkeypatch import MonkeyPatch

from backend.common import tasklets


def test_enable_is_noop_without_help_tasklet_along(monkeypatch: MonkeyPatch) -> None:
    class FutureWithoutHelp:
        def __init__(self) -> None:
            pass

    original_init = FutureWithoutHelp.__init__
    monkeypatch.setattr(tasklets, "_tasklet_context_propagation_enabled", False)
    monkeypatch.setattr(
        tasklets, "ndb_tasklets", SimpleNamespace(Future=FutureWithoutHelp)
    )

    tasklets.enable_tasklet_context_propagation()

    assert FutureWithoutHelp.__init__ is original_init


def test_help_tasklet_along_without_captured_context(
    monkeypatch: MonkeyPatch,
) -> None:
    calls: List[Any] = []

    class FakeFuture:
        def __init__(self) -> None:
            pass

        def _help_tasklet_along(self) -> str:
            calls.append(contextvars.copy_context())
            return "helped"

    monkeypatch.setattr(tasklets, "_tasklet_context_propagation_enabled", False)
    monkeypatch.setattr(tasklets, "ndb_tasklets", SimpleNamespace(Future=FakeFuture))
    tasklets.enable_tasklet_context_propagation()

    future: Any = FakeFuture()
    assert future._py_context is not None
    assert future._help_tasklet_along() == "helped"

    # Futures created before the patch have no captured context
    del future._py_context
    assert future._help_tasklet_along() == "helped"
    assert len(calls) == 2

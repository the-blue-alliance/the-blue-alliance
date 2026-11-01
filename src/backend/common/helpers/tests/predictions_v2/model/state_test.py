import io
from typing import Any, Dict

import numpy as np
import pytest

from backend.common.helpers.predictions_v2.model import state
from backend.common.helpers.predictions_v2.model.config import (
    DEFAULT_CONFIG,
    HKFConfig,
)


@state.register_state
class _Node:
    def __init__(self, value: Any, child: Any = None) -> None:
        self.value = value
        self.child = child
        self.cfg = DEFAULT_CONFIG


@state.register_state
class _Slotted:
    __slots__ = ("a", "b")

    def __init__(self, a: Any, b: Any) -> None:
        self.a = a
        self.b = b


class _Unregistered:
    pass


def _round_trip(obj: Any, cfg: HKFConfig = DEFAULT_CONFIG) -> Any:
    return state.decode(state.encode(obj, "fp"), "fp", cfg)


def test_round_trip_keeps_values_and_types() -> None:
    value: Dict[Any, Any] = {
        "floats": [0.1, 1e-300, -2.5, float("inf")],
        "ints": (1, -2, 3),
        ("event", "frc254"): 4,
        (1, True): None,
        "array": np.arange(6, dtype=float).reshape(2, 3),
        "np_scalar": np.float64(0.3),
        "np_int": np.int64(7),
        "empty": {},
    }
    out = _round_trip(_Node(value))

    assert isinstance(out, _Node)
    assert out.value["floats"] == [0.1, 1e-300, -2.5, float("inf")]
    assert out.value["ints"] == (1, -2, 3)
    assert out.value[("event", "frc254")] == 4
    assert out.value[(1, True)] is None
    np.testing.assert_array_equal(out.value["array"], value["array"])
    assert type(out.value["np_scalar"]) is np.float64
    assert type(out.value["np_int"]) is np.int64
    assert out.value["empty"] == {}


def test_round_trip_keeps_shared_references_and_slots() -> None:
    shared = _Node(1)
    root = _Node([shared, shared], child=_Slotted(shared, np.ones(2)))
    out = _round_trip(root)

    assert out.value[0] is out.value[1]
    assert out.child.a is out.value[0]
    np.testing.assert_array_equal(out.child.b, np.ones(2))


def test_config_is_never_stored() -> None:
    cfg = HKFConfig(pcg_reg=3.0)
    out = _round_trip(_Node(1), cfg)
    assert out.cfg is cfg


def test_unregistered_class_is_rejected() -> None:
    with pytest.raises(TypeError):
        state.encode(_Node(_Unregistered()), "fp")


def test_version_and_fingerprint_are_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    blob = state.encode(_Node(1), "fp")
    with pytest.raises(state.StateVersionError):
        state.decode(blob, "other", DEFAULT_CONFIG)
    monkeypatch.setattr(state, "STATE_VERSION", state.STATE_VERSION + 1)
    with pytest.raises(state.StateVersionError):
        state.decode(blob, "fp", DEFAULT_CONFIG)


def test_object_arrays_are_not_loaded() -> None:
    buf = io.BytesIO()
    np.savez(
        buf,
        header=np.frombuffer(b"{}", dtype=np.uint8),
        a0=np.array([{}], dtype=object),
    )
    with pytest.raises(ValueError):
        state.decode(buf.getvalue(), "fp", DEFAULT_CONFIG)


def test_fingerprint_depends_on_config_and_tables() -> None:
    base = state.fingerprint(DEFAULT_CONFIG, {"a": 1})
    assert base == state.fingerprint(HKFConfig(), {"a": 1})
    assert base != state.fingerprint(HKFConfig(pcg_reg=3.0), {"a": 1})
    assert base != state.fingerprint(DEFAULT_CONFIG, {"a": 2})

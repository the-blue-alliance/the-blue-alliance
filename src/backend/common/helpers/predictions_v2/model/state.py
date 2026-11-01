"""Serialization of the predictor state without pickle.

The encoded state is a compressed ``.npz`` archive: every numpy array is its own entry, and
an entry named ``header`` holds the rest of the object graph as UTF-8 JSON. Only the types
below can be encoded, and only classes registered with ``register_state`` can be rebuilt:

* None, bool, int, float, str, numpy scalars and arrays
* list, tuple and dict (any encodable keys)
* instances of registered classes (all attributes, shared references kept)
* ``HKFConfig``: never stored. A loaded state uses the configuration in code.

The header records ``STATE_VERSION`` and a fingerprint of the configuration and rulebook.
``decode`` raises ``StateVersionError`` when either differs, so a state written by another
model version is replayed from the match log instead of loaded.
"""

import dataclasses
import hashlib
import io
import json
from typing import Any, Dict, List, Type, TypeVar

import numpy as np

from backend.common.helpers.predictions_v2.model.config import HKFConfig

STATE_VERSION = 1

_REGISTRY: Dict[str, Type[Any]] = {}

T = TypeVar("T")


class StateVersionError(Exception):
    pass


def register_state(cls: Type[T]) -> Type[T]:
    """Allow instances of ``cls`` in an encoded state."""
    _REGISTRY[cls.__name__] = cls
    return cls


def fingerprint(config: HKFConfig, *tables: Any) -> str:
    """Stable hash of the configuration and the rulebook tables."""
    blob = json.dumps(
        [dataclasses.asdict(config), [repr(t) for t in tables]], sort_keys=True
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _attrs(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    out: Dict[str, Any] = {}
    for klass in type(obj).__mro__:
        for name in getattr(klass, "__slots__", ()):
            if hasattr(obj, name):
                out[name] = getattr(obj, name)
    return out


class _Encoder:
    def __init__(self) -> None:
        self.arrays: List[np.ndarray] = []
        self.objects: Dict[int, int] = {}

    def enc(self, v: Any) -> Any:
        if v is None or isinstance(v, (bool, str)):
            return v
        if isinstance(v, np.ndarray):
            self.arrays.append(v)
            return {"$a": len(self.arrays) - 1}
        if isinstance(v, np.generic):
            return {"$n": v.dtype.str, "v": v.item()}
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, list):
            return [self.enc(x) for x in v]
        if isinstance(v, tuple):
            return {"$t": [self.enc(x) for x in v]}
        if isinstance(v, dict):
            return {"$d": [[self.enc(k), self.enc(x)] for k, x in v.items()]}
        if isinstance(v, HKFConfig):
            return {"$c": 1}
        name = type(v).__name__
        if _REGISTRY.get(name) is not type(v):
            raise TypeError(f"cannot encode {type(v)!r}")
        oid = self.objects.get(id(v))
        if oid is not None:
            return {"$r": oid}
        oid = len(self.objects)
        self.objects[id(v)] = oid
        return {
            "$o": name,
            "id": oid,
            "f": {k: self.enc(x) for k, x in _attrs(v).items()},
        }


class _Decoder:
    def __init__(self, arrays: Dict[str, np.ndarray], config: HKFConfig) -> None:
        self.arrays = arrays
        self.config = config
        self.objects: Dict[int, Any] = {}

    def dec(self, v: Any) -> Any:
        if isinstance(v, list):
            return [self.dec(x) for x in v]
        if not isinstance(v, dict):
            return v
        if "$a" in v:
            return self.arrays[f"a{v['$a']}"]
        if "$n" in v:
            return np.dtype(v["$n"]).type(v["v"])
        if "$t" in v:
            return tuple(self.dec(x) for x in v["$t"])
        if "$d" in v:
            return {self.dec(k): self.dec(x) for k, x in v["$d"]}
        if "$c" in v:
            return self.config
        if "$r" in v:
            return self.objects[v["$r"]]
        cls = _REGISTRY.get(v["$o"])
        if cls is None:
            raise StateVersionError(f"unknown state class {v['$o']}")
        obj = cls.__new__(cls)
        self.objects[v["id"]] = obj
        for k, x in v["f"].items():
            object.__setattr__(obj, k, self.dec(x))
        return obj


def encode(root: Any, model_fingerprint: str) -> bytes:
    e = _Encoder()
    tree = e.enc(root)
    header = json.dumps(
        {"version": STATE_VERSION, "fingerprint": model_fingerprint, "state": tree},
        separators=(",", ":"),
    ).encode()
    buf = io.BytesIO()
    entries = {f"a{i}": a for i, a in enumerate(e.arrays)}
    np.savez_compressed(buf, header=np.frombuffer(header, dtype=np.uint8), **entries)
    return buf.getvalue()


def decode(blob: bytes, model_fingerprint: str, config: HKFConfig) -> Any:
    with np.load(io.BytesIO(blob), allow_pickle=False) as npz:
        arrays = {k: npz[k] for k in npz.files}
    header = json.loads(arrays.pop("header").tobytes().decode())
    if header.get("version") != STATE_VERSION:
        raise StateVersionError(f"state version {header.get('version')}")
    if header.get("fingerprint") != model_fingerprint:
        raise StateVersionError("state written with another model configuration")
    return _Decoder(arrays, config).dec(header["state"])

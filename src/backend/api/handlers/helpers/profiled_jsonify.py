from typing import Generic, TypeVar

from flask import jsonify, Response

from backend.common.profiler import Span

T = TypeVar("T")


class TypedFlaskResponse(Response, Generic[T]):
    pass


def profiled_jsonify(obj: T) -> TypedFlaskResponse[T]:
    with Span("profiled_jsonify"):
        return jsonify(obj)  # type: ignore[return-value]

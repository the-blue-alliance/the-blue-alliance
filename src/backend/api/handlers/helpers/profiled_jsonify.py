from typing import Generic, TypeVar, Union

from flask import current_app, jsonify, Response

from backend.common.profiler import Span

T = TypeVar("T")


class TypedFlaskResponse(Response, Generic[T]):
    pass


def profiled_jsonify(obj: Union[T, bytes, bytearray]) -> TypedFlaskResponse[T]:
    with Span("profiled_jsonify"):
        if isinstance(obj, (bytes, bytearray)):
            return current_app.response_class(  # pyre-ignore[7]
                bytes(obj),
                mimetype="application/json",
            )  # type: ignore[return-value]
        return jsonify(obj)  # type: ignore[return-value]

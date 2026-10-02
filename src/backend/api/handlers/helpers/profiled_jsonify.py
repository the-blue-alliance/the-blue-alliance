import logging
from typing import Generic, TypeVar, Union

import orjson
from flask import current_app, jsonify, Response

from backend.common.profiler import Span

T = TypeVar("T")


class TypedFlaskResponse(Response, Generic[T]):
    pass


def profiled_jsonify(obj: Union[T, bytes, bytearray]) -> TypedFlaskResponse[T]:
    with Span("profiled_jsonify") as span:
        if isinstance(obj, (bytes, bytearray)):
            span.set_label("input_type", "bytes")
            span.set_label("response_size_bytes", str(len(obj)))
            return current_app.response_class(  # pyre-ignore[7]
                bytes(obj),
                mimetype="application/json",
            )  # type: ignore[return-value]
        try:
            span.set_label("input_type", type(obj).__name__)
            payload = orjson.dumps(obj)
            span.set_label("response_size_bytes", str(len(payload)))
            return current_app.response_class(  # pyre-ignore[7]
                payload,
                mimetype="application/json",
            )  # type: ignore[return-value]
        except (orjson.JSONEncodeError, TypeError) as e:
            logging.warning(
                f"orjson.dumps failed in profiled_jsonify, falling back to jsonify: {e}"
            )
            span.set_label("fallback", "jsonify")
            return jsonify(obj)  # type: ignore[return-value]

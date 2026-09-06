import logging
from typing import Generic, TypeVar, Union

import orjson
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
        try:
            payload = orjson.dumps(obj)
            return current_app.response_class(  # pyre-ignore[7]
                payload,
                mimetype="application/json",
            )  # type: ignore[return-value]
        except (orjson.JSONEncodeError, TypeError) as e:
            logging.warning(
                f"orjson.dumps failed in profiled_jsonify, falling back to jsonify: {e}"
            )
            return jsonify(obj)  # type: ignore[return-value]

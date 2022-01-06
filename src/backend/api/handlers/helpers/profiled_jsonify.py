from typing import Any

from flask import jsonify, Response

from backend.common.profiler import Span


def profiled_jsonify(obj: Any) -> Response:
    with Span("profiled_jsonify"):
        return jsonify(obj)

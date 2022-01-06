from flask import Response

from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify


def make_error_response(status_code: int, error_dict: dict) -> Response:
    response = profiled_jsonify(error_dict)
    response.status_code = status_code
    return response

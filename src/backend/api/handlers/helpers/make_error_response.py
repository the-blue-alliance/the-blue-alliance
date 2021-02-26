from flask import jsonify, Response


def make_error_response(status_code: int, error_dict: dict) -> Response:
    response = jsonify(error_dict)
    response.status_code = status_code
    return response

from typing import Union

from flask import Response

from backend.api.handlers.helpers.make_error_response import make_error_response


def handle_404(_e: Union[int, Exception]) -> Response:
    return make_error_response(404, {"Error": "Invalid endpoint"})

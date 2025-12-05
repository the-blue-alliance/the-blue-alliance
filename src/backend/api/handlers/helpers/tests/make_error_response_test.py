import json

import pytest
from flask import Flask

from backend.api.handlers.helpers.make_error_response import make_error_response


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    return app


def test_make_error_response(app: Flask) -> None:
    with app.app_context():
        error_dict = {"Error": "Not found"}
        response = make_error_response(404, error_dict)

        assert response.status_code == 404
        assert response.content_type == "application/json"
        assert json.loads(response.data) == error_dict


def test_make_error_response_different_status_codes(app: Flask) -> None:
    with app.app_context():
        error_dict = {"Error": "Bad request"}
        response = make_error_response(400, error_dict)
        assert response.status_code == 400

        error_dict = {"Error": "Unauthorized"}
        response = make_error_response(401, error_dict)
        assert response.status_code == 401

        error_dict = {"Error": "Internal server error"}
        response = make_error_response(500, error_dict)
        assert response.status_code == 500


def test_make_error_response_complex_error_dict(app: Flask) -> None:
    with app.app_context():
        error_dict = {
            "Error": "Validation failed",
            "details": ["field1 is required", "field2 must be a number"],
            "code": 1001,
        }
        response = make_error_response(422, error_dict)

        assert response.status_code == 422
        assert json.loads(response.data) == error_dict

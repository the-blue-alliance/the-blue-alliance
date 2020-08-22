import pytest
from flask import Flask


@pytest.fixture
def empty_app() -> Flask:
    return Flask(__name__)


@pytest.fixture
def secret_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "secret_key"
    return app

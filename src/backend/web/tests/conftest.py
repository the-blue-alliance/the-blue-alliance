import pytest
from flask import Flask


@pytest.fixture
def empty_app() -> Flask:
    return Flask(__name__)

import pytest
from flask import Flask


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)

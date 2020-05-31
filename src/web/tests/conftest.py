from flask import Flask
import pytest


@pytest.fixture
def empty_app() -> Flask:
    return Flask(__name__)

from flask import Flask
import pytest


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)

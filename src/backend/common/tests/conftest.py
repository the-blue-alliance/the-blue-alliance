import pytest
from flask import Flask


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass

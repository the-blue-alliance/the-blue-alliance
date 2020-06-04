import pytest

from google.cloud import ndb
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True)
def init_ndb_env_vars(monkeypatch: MonkeyPatch) -> None:
    """
    Initializing an ndb Client in a test env requires some environment variables to be set
    For now, these are just garbage values intended to give the library _something_
    (we don't expect them to actually work yet)
    """

    monkeypatch.setenv("DATASTORE_EMULATOR_HOST", "localhost:8432")
    monkeypatch.setenv("DATASTORE_DATASET", "tba-unit-test")


@pytest.fixture()
def ndb_context(init_ndb_env_vars):
    client = ndb.Client()
    with client.context() as context:
        yield context

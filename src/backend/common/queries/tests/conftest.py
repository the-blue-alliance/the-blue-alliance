from google.cloud import ndb
import pytest


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context: ndb.Context) -> None:
    pass

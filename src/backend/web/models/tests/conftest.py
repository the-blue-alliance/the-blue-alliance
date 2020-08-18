import pytest

from google.cloud import ndb


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context: ndb.Context) -> None:
    pass

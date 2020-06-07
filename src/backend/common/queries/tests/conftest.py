import pytest


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context):
    pass

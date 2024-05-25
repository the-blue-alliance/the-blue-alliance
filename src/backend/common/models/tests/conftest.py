import pytest


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture(autouse=True)
def auto_add_taskqueue_stub(taskqueue_stub) -> None:
    pass

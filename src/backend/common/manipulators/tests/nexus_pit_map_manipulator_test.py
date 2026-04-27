import unittest

import pytest

from backend.common.manipulators.nexus_pit_map_manipulator import NexusPitMapManipulator
from backend.common.models.nexus_pit_map import NexusPitMap


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestNexusPitMapManipulator(unittest.TestCase):
    def setUp(self):
        self.old_model = NexusPitMap(
            id="2026casj",
            data_json={"size": {"x": 10, "y": 20}},
        )
        self.new_model = NexusPitMap(
            id="2026casj",
            data_json={"size": {"x": 20, "y": 40}, "pits": {}},
        )

    def test_create_or_update(self):
        NexusPitMapManipulator.createOrUpdate(self.old_model)
        created = NexusPitMap.get_by_id("2026casj")
        assert created is not None
        assert created.data_json == {"size": {"x": 10, "y": 20}}

        NexusPitMapManipulator.createOrUpdate(self.new_model)
        updated = NexusPitMap.get_by_id("2026casj")
        assert updated is not None
        assert updated.data_json == {"size": {"x": 20, "y": 40}, "pits": {}}

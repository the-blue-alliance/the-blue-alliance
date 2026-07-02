import unittest

import pytest

from backend.common.manipulators.nexus_event_details_manipulator import (
    NexusEventDetailsManipulator,
)
from backend.common.models.nexus_event_details import NexusEventDetails


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestNexusEventDetailsManipulator(unittest.TestCase):
    def setUp(self):
        self.old_model = NexusEventDetails(
            id="2026casj",
            pitmap_json={"size": {"x": 10, "y": 20}},
        )
        self.new_model = NexusEventDetails(
            id="2026casj",
            pitmap_json={"size": {"x": 20, "y": 40}, "pits": {}},
        )

    def test_create_or_update(self):
        NexusEventDetailsManipulator.createOrUpdate(self.old_model)
        created = NexusEventDetails.get_by_id("2026casj")
        assert created is not None
        assert created.pitmap_json == {"size": {"x": 10, "y": 20}}

        NexusEventDetailsManipulator.createOrUpdate(self.new_model)
        updated = NexusEventDetails.get_by_id("2026casj")
        assert updated is not None
        assert updated.pitmap_json == {"size": {"x": 20, "y": 40}, "pits": {}}

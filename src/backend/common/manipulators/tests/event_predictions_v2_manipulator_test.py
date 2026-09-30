import unittest

import pytest

from backend.common.manipulators.event_predictions_v2_manipulator import (
    EventPredictionsV2Manipulator,
)
from backend.common.models.event_predictions_v2 import EventPredictionsV2


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestEventPredictionsV2Manipulator(unittest.TestCase):
    def setUp(self):
        self.old_model = EventPredictionsV2(
            id="2024casj",
            model_version="hkf_ev_pcg_v1.0",
            as_of_match="2024casj_qm1",
            predictions={
                "model_version": "hkf_ev_pcg_v1.0",
                "as_of_match": "2024casj_qm1",
                "last_updated": "2024-03-30T12:00:00Z",
                "matches": {},
                "team_ratings": {},
            },
        )
        self.new_model = EventPredictionsV2(
            id="2024casj",
            model_version="hkf_ev_pcg_v1.0",
            as_of_match="2024casj_qm2",
            predictions={
                "model_version": "hkf_ev_pcg_v1.0",
                "as_of_match": "2024casj_qm2",
                "last_updated": "2024-03-30T12:15:00Z",
                "matches": {"2024casj_qm2": {}},
                "team_ratings": {"frc254": {}},
            },
        )

    def test_create_or_update(self):
        EventPredictionsV2Manipulator.createOrUpdate(self.old_model)
        created = EventPredictionsV2.get_by_id("2024casj")
        assert created is not None
        assert created.as_of_match == "2024casj_qm1"

        EventPredictionsV2Manipulator.createOrUpdate(self.new_model)
        updated = EventPredictionsV2.get_by_id("2024casj")
        assert updated is not None
        assert updated.as_of_match == "2024casj_qm2"
        assert "2024casj_qm2" in updated.predictions["matches"]

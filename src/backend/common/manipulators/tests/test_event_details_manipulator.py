import unittest

import pytest

from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.models.event_details import EventDetails


@pytest.mark.usefixtures("ndb_context")
class TestEventDetailsManipulator(unittest.TestCase):
    def setUp(self):
        self.old_alliance_selections = {
            "1": {"picks": ["frc254", "frc469", "frc2848", "frc74"], "declines": []},
            "2": {"picks": ["frc1718", "frc2451", "frc573", "frc2016"], "declines": []},
            "3": {"picks": ["frc2928", "frc2013", "frc1311", "frc842"], "declines": []},
            "4": {"picks": ["frc180", "frc125", "frc1323", "frc2468"], "declines": []},
            "5": {"picks": ["frc118", "frc359", "frc4334", "frc865"], "declines": []},
            "6": {"picks": ["frc135", "frc1241", "frc11", "frc68"], "declines": []},
            "7": {"picks": ["frc3478", "frc177", "frc294", "frc230"], "declines": []},
            "8": {"picks": ["frc624", "frc987", "frc3476", "frc123"], "declines": []},
        }

        self.new_alliance_selections = {
            "1": {"picks": ["frc254", "frc469", "frc2848", "frc74"], "declines": []},
            "2": {"picks": ["frc1718", "frc2451", "frc573", "frc2016"], "declines": []},
            "3": {"picks": ["frc2928", "frc2013", "frc1311", "frc842"], "declines": []},
            "4": {"picks": ["frc180", "frc125", "frc1323", "frc2468"], "declines": []},
            "5": {"picks": ["frc118", "frc359", "frc4334", "frc865"], "declines": []},
            "6": {"picks": ["frc135", "frc1241", "frc11", "frc68"], "declines": []},
            "7": {"picks": ["frc3478", "frc177", "frc294", "frc230"], "declines": []},
            "8": {"picks": ["frc624", "frc987", "frc3476", "frc3015"], "declines": []},
        }

        self.old_event_details = EventDetails(
            id="2011ct", alliance_selections=self.old_alliance_selections,
        )

        self.new_event_details = EventDetails(
            id="2011ct",
            alliance_selections=self.new_alliance_selections,
            matchstats={
                "oprs": {
                    "4255": 7.4877151786460301,
                    "2643": 27.285682906835952,
                    "852": 10.452538750544525,
                    "4159": 25.820137009871139,
                    "581": 18.513816255143144,
                }
            },
        )

    def assertMergedEventDetails(self, event_details):
        self.assertOldEventDetails(event_details)
        self.assertEqual(
            event_details.matchstats,
            {
                "oprs": {
                    "4255": 7.4877151786460301,
                    "2643": 27.285682906835952,
                    "852": 10.452538750544525,
                    "4159": 25.820137009871139,
                    "581": 18.513816255143144,
                }
            },
        )
        self.assertEqual(
            event_details.alliance_selections, self.new_alliance_selections
        )

    def assertOldEventDetails(self, event_details):
        self.assertEqual(event_details.key.id(), "2011ct")

    def test_createOrUpdate(self):
        EventDetailsManipulator.createOrUpdate(self.old_event_details)
        self.assertOldEventDetails(EventDetails.get_by_id("2011ct"))
        EventDetailsManipulator.createOrUpdate(self.new_event_details)
        self.assertMergedEventDetails(EventDetails.get_by_id("2011ct"))

    def test_findOrSpawn(self):
        self.old_event_details.put()
        self.assertMergedEventDetails(
            EventDetailsManipulator.findOrSpawn(self.new_event_details)
        )

    def test_updateMerge(self):
        self.assertMergedEventDetails(
            EventDetailsManipulator.updateMerge(
                self.new_event_details, self.old_event_details
            )
        )

import unittest2

from consts.event_type import EventType
from helpers.event_helper import EventHelper


@unittest2.skip
class TestUsfirstEventTypeParser(unittest2.TestCase):
    def test_parse(self):
        self.assertEqual(EventHelper.parseEventType("Regional"), EventType.REGIONAL)
        self.assertEqual(EventHelper.parseEventType("regional"), EventType.REGIONAL)

        self.assertEqual(EventHelper.parseEventType("District"), EventType.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("district"), EventType.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("MI District"), EventType.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("District Event"), EventType.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("Qualifying Event"), EventType.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("Qualifier"), EventType.DISTRICT)

        self.assertEqual(EventHelper.parseEventType("District Championship"), EventType.DISTRICT_CMP)
        self.assertEqual(EventHelper.parseEventType("MI FRC State Championship"), EventType.DISTRICT_CMP)
        self.assertEqual(EventHelper.parseEventType("Qualifying Championship"), EventType.DISTRICT_CMP)

        self.assertEqual(EventHelper.parseEventType("Championship Division"), EventType.CMP_DIVISION)

        self.assertEqual(EventHelper.parseEventType("Championship Finals"), EventType.CMP_FINALS)
        self.assertEqual(EventHelper.parseEventType("Championship"), EventType.CMP_FINALS)

        self.assertEqual(EventHelper.parseEventType("Offseason"), EventType.OFFSEASON)
        self.assertEqual(EventHelper.parseEventType("Preseason"), EventType.PRESEASON)

        self.assertEqual(EventHelper.parseEventType("Division"), EventType.UNLABLED)

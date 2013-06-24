import unittest2

from models.event import Event
from helpers.event_helper import EventHelper

class TestUsfirstEventTypeParser(unittest2.TestCase):
    def test_parse(self):
        self.assertEqual(EventHelper.parseEventType("Regional"), Event.REGIONAL)
        self.assertEqual(EventHelper.parseEventType("regional"), Event.REGIONAL)
        
        self.assertEqual(EventHelper.parseEventType("District"), Event.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("district"), Event.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("MI District"), Event.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("District Event"), Event.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("Qualifying Event"), Event.DISTRICT)
        self.assertEqual(EventHelper.parseEventType("Qualifier"), Event.DISTRICT)
        
        self.assertEqual(EventHelper.parseEventType("District Championship"), Event.DISTRICT_CMP)
        self.assertEqual(EventHelper.parseEventType("MI FRC State Championship"), Event.DISTRICT_CMP)
        self.assertEqual(EventHelper.parseEventType("Qualifying Championship"), Event.DISTRICT_CMP)
        
        self.assertEqual(EventHelper.parseEventType("Championship Division"), Event.CMP_DIVISION)
        self.assertEqual(EventHelper.parseEventType("Division"), Event.CMP_DIVISION)
        
        self.assertEqual(EventHelper.parseEventType("Championship Finals"), Event.CMP_FINALS)
        self.assertEqual(EventHelper.parseEventType("Championship"), Event.CMP_FINALS)

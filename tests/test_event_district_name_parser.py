import unittest2

from tba.consts.district_type import DistrictType
from helpers.event_helper import EventHelper


class TestEventDistrictNameParser(unittest2.TestCase):
    def test_event_parse_district_name(self):
        """
        A bunch of tests from various years
        """
        self.assertEqual(EventHelper.parseDistrictName('FIRST in Michigan'), DistrictType.MICHIGAN)
        self.assertEqual(EventHelper.parseDistrictName('Mid-Atlantic Robotics'), DistrictType.MID_ATLANTIC)
        self.assertEqual(EventHelper.parseDistrictName('New England'), DistrictType.NEW_ENGLAND)
        self.assertEqual(EventHelper.parseDistrictName('Pacific Northwest'), DistrictType.PACIFIC_NORTHWEST)
        self.assertEqual(EventHelper.parseDistrictName('IndianaFIRST'), DistrictType.INDIANA)
        self.assertEqual(EventHelper.parseDistrictName('Not a valid district'), DistrictType.NO_DISTRICT)
        self.assertEqual(EventHelper.parseDistrictName('California'), DistrictType.NO_DISTRICT)
        self.assertEqual(EventHelper.parseDistrictName(None), DistrictType.NO_DISTRICT)
        self.assertEqual(EventHelper.parseDistrictName(''), DistrictType.NO_DISTRICT)

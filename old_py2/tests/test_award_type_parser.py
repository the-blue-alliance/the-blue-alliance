import unittest2
import csv
import json
import StringIO

from consts.award_type import AwardType
from helpers.award_helper import AwardHelper


class TestUsfirstEventTypeParser(unittest2.TestCase):
    def test_parse(self):
        """
        Tests for a select subset of award types. Add more if desired.
        """
        # Make sure all old regional awards have matching types
        with open('test_data/pre_2002_regional_awards.csv', 'r') as f:
            csv_data = list(csv.reader(StringIO.StringIO(f.read()), delimiter=',', skipinitialspace=True))
            for award in csv_data:
                self.assertNotEqual(AwardHelper.parse_award_type(award[2]), None)

        # Make sure all old regional awards have matching types
        with open('test_data/pre_2007_cmp_awards.csv', 'r') as f:
            csv_data = list(csv.reader(StringIO.StringIO(f.read()), delimiter=',', skipinitialspace=True))
            for award in csv_data:
                self.assertNotEqual(AwardHelper.parse_award_type(award[2]), None)

        # test 2015 award names
        with open('test_data/fms_api/2015_award_types.json', 'r') as f:
            for award in json.loads(f.read()):
                self.assertNotEqual(AwardHelper.parse_award_type(award['description']), None)

        # test 2017 award types
        with open('test_data/fms_api/2017_award_types.json', 'r') as f:
            for award in json.loads(f.read()):
                self.assertNotEqual(AwardHelper.parse_award_type(award['description']), None)

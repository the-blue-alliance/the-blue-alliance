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
        self.assertEqual(AwardHelper.parse_award_type("Chairman's"), AwardType.CHAIRMANS)
        self.assertEqual(AwardHelper.parse_award_type("Chairman"), AwardType.CHAIRMANS)
        self.assertEqual(AwardHelper.parse_award_type("Chairman's Award Finalist"), AwardType.CHAIRMANS_FINALIST)

        self.assertEqual(AwardHelper.parse_award_type("Winner #1"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Division Winner #2"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Newton - Division Champion #3"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Championship Winner #3"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Championship Champion #4"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Championship Champion"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Championship Winner"), AwardType.WINNER)
        self.assertEqual(AwardHelper.parse_award_type("Winner"), AwardType.WINNER)

        self.assertEqual(AwardHelper.parse_award_type("Finalist #1"), AwardType.FINALIST)
        self.assertEqual(AwardHelper.parse_award_type("Division Finalist #2"), AwardType.FINALIST)
        self.assertEqual(AwardHelper.parse_award_type("Championship Finalist #3"), AwardType.FINALIST)
        self.assertEqual(AwardHelper.parse_award_type("Championship Finalist #4"), AwardType.FINALIST)
        self.assertEqual(AwardHelper.parse_award_type("Championship Finalist"), AwardType.FINALIST)
        self.assertEqual(AwardHelper.parse_award_type("Finalist"), AwardType.FINALIST)

        self.assertEqual(AwardHelper.parse_award_type("Dean's List Finalist #1"), AwardType.DEANS_LIST)
        self.assertEqual(AwardHelper.parse_award_type("Dean's List Finalist"), AwardType.DEANS_LIST)
        self.assertEqual(AwardHelper.parse_award_type("Dean's List Winner #9"), AwardType.DEANS_LIST)
        self.assertEqual(AwardHelper.parse_award_type("Dean's List Winner"), AwardType.DEANS_LIST)
        self.assertEqual(AwardHelper.parse_award_type("Dean's List"), AwardType.DEANS_LIST)

        self.assertEqual(AwardHelper.parse_award_type("Excellence in Design Award sponsored by Autodesk (3D CAD)"), AwardType.EXCELLENCE_IN_DESIGN_CAD)
        self.assertEqual(AwardHelper.parse_award_type("Excellence in Design Award sponsored by Autodesk (Animation)"), AwardType.EXCELLENCE_IN_DESIGN_ANIMATION)
        self.assertEqual(AwardHelper.parse_award_type("Excellence in Design Award"), AwardType.EXCELLENCE_IN_DESIGN)

        self.assertEqual(AwardHelper.parse_award_type("Dr. Bart Kamen Memorial Scholarship #1"), AwardType.BART_KAMEN_MEMORIAL)
        self.assertEqual(AwardHelper.parse_award_type("Media and Technology Award sponsored by Comcast"), AwardType.MEDIA_AND_TECHNOLOGY)
        self.assertEqual(AwardHelper.parse_award_type("Make It Loud Award"), AwardType.MAKE_IT_LOUD)
        self.assertEqual(AwardHelper.parse_award_type("Founder's Award"), AwardType.FOUNDERS)
        self.assertEqual(AwardHelper.parse_award_type("Championship - Web Site Award"), AwardType.WEBSITE)
        self.assertEqual(AwardHelper.parse_award_type("Recognition of Extraordinary Service"), AwardType.RECOGNITION_OF_EXTRAORDINARY_SERVICE)
        self.assertEqual(AwardHelper.parse_award_type("Outstanding Cart Award"), AwardType.OUTSTANDING_CART)
        self.assertEqual(AwardHelper.parse_award_type("Wayne State University Aim Higher Award"), AwardType.WSU_AIM_HIGHER)
        self.assertEqual(AwardHelper.parse_award_type("Delphi \"Driving Tommorow's Technology\" Award"), AwardType.DRIVING_TOMORROWS_TECHNOLOGY)
        self.assertEqual(AwardHelper.parse_award_type("Delphi Drive Tommorows Technology"), AwardType.DRIVING_TOMORROWS_TECHNOLOGY)
        self.assertEqual(AwardHelper.parse_award_type("Kleiner, Perkins, Caufield and Byers"), AwardType.ENTREPRENEURSHIP)
        self.assertEqual(AwardHelper.parse_award_type("Leadership in Control Award"), AwardType.LEADERSHIP_IN_CONTROL)
        self.assertEqual(AwardHelper.parse_award_type("#1 Seed"), AwardType.NUM_1_SEED)
        self.assertEqual(AwardHelper.parse_award_type("Incredible Play Award"), AwardType.INCREDIBLE_PLAY)
        self.assertEqual(AwardHelper.parse_award_type("People's Choice Animation Award"), AwardType.PEOPLES_CHOICE_ANIMATION)
        self.assertEqual(AwardHelper.parse_award_type("Autodesk Award for Visualization - Grand Prize"), AwardType.VISUALIZATION)
        self.assertEqual(AwardHelper.parse_award_type("Autodesk Award for Visualization - Rising Star"), AwardType.VISUALIZATION_RISING_STAR)

        self.assertEqual(AwardHelper.parse_award_type("Some Random Award Winner"), None)
        self.assertEqual(AwardHelper.parse_award_type("Random Champion"), None)
        self.assertEqual(AwardHelper.parse_award_type("An Award"), None)

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

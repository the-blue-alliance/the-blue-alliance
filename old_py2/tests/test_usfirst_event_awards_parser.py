import unittest2
import json

from consts.award_type import AwardType
from datafeeds.usfirst_event_awards_parser import UsfirstEventAwardsParser


def convert_to_comparable(data):
    """
    Converts jsons to dicts so that elements can be more easily compared
    """
    if type(data) == list:
        return [convert_to_comparable(e) for e in data]
    elif type(data) == dict:
        to_return = {}
        for key, value in data.items():
            to_return[key] = convert_to_comparable(value)
        return to_return
    elif type(data) == str or type(data) == unicode:
        try:
            return json.loads(data)
        except ValueError:
            return data
    else:
        return data


@unittest2.skip
class TestUsfirstEventAwardsParser(unittest2.TestCase):
    def test_parse_regional_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 26)
        self.assertEqual(len(awards), 21)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [604],
            'recipient_json_list': [{'team_number': 604, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [1280, 1516, 190],
            'recipient_json_list': [{'team_number': 1280, 'awardee': None},
                                    {'team_number': 1516, 'awardee': None},
                                    {'team_number': 190, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Yang Xie \u2013 Team 846"}],
        }
        self.assertTrue(individual_award in awards)

    def test_parse_regional_2010(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2010sac.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 29)
        self.assertEqual(len(awards), 24)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [604],
            'recipient_json_list': [{'team_number': 604, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Outstanding Volunteer of the Year",
            'award_type_enum': AwardType.VOLUNTEER,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Gary Blakesley"}],
        }
        self.assertTrue(individual_award in awards)

        # Test Team and Individual Award
        team_and_individual_award = {
            'name_str': "Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [604],
            'recipient_json_list': [{'team_number': 604, 'awardee': u"Helen Arrington"}],
        }
        self.assertTrue(team_and_individual_award in awards)

    def test_parse_regional_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 28)
        self.assertEqual(len(awards), 23)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [604],
            'recipient_json_list': [{'team_number': 604, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Volunteer of the Year",
            'award_type_enum': AwardType.VOLUNTEER,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Joanne Heberer"}],
        }
        self.assertTrue(individual_award in awards)

        # Test Team and Individual Award
        team_and_individual_award = {
            'name_str': "Woodie Flowers Finalist Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [604],
            'recipient_json_list': [{'team_number': 604, 'awardee': u"Jim Mori"}],
        }
        self.assertTrue(team_and_individual_award in awards)

    def test_parse_district_championship_2009(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2009gl.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 30)
        self.assertEqual(len(awards), 21)

        awards = convert_to_comparable(awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "State Championship Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [27, 33, 217],
            'recipient_json_list': [{'team_number': 27, 'awardee': None},
                                    {'team_number': 33, 'awardee': None},
                                    {'team_number': 217, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Jennifer Harvey of Team 503"}],
        }
        self.assertTrue(individual_award in awards)

    def test_parse_district_championship_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012gl.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 34)
        self.assertEqual(len(awards), 22)

        awards = convert_to_comparable(awards)

        # Test Muti Team Award
        multi_team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [33, 503, 27],
            'recipient_json_list': [{'team_number': 33, 'awardee': None},
                                    {'team_number': 503, 'awardee': None},
                                    {'team_number': 27, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

        # Test Multi Team and Individual Award
        multi_team_and_individual_award = {
            'name_str': "FIRST Dean's List Finalist Award",
            'award_type_enum': AwardType.DEANS_LIST,
            'team_number_list': [3538, 548, 2834, 33, 862, 1684],
            'recipient_json_list': [{'team_number': 3538, 'awardee': u"Jaris Dingman"},
                                    {'team_number': 548, 'awardee': u"Claire Goolsby"},
                                    {'team_number': 2834, 'awardee': u"Ryan Hoyt"},
                                    {'team_number': 33, 'awardee': u"Andrew Palardy"},
                                    {'team_number': 862, 'awardee': u"Ian Pudney"},
                                    {'team_number': 1684, 'awardee': u"Matthew Wagner"}],
        }
        self.assertTrue(multi_team_and_individual_award in awards)

    def test_parse_championship_divison_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007galileo.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 7)
        self.assertEqual(len(awards), 3)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Galileo - Highest Rookie Seed",
            'award_type_enum': AwardType.HIGHEST_ROOKIE_SEED,
            'team_number_list': [2272],
            'recipient_json_list': [{'team_number': 2272, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Galileo - Division Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [173, 1319, 1902],
            'recipient_json_list': [{'team_number': 173, 'awardee': None},
                                    {'team_number': 1319, 'awardee': None},
                                    {'team_number': 1902, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

    def test_parse_championship_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 29)
        self.assertEqual(len(awards), 23)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Championship - Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [365],
            'recipient_json_list': [{'team_number': 365, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Championship - FRC Outstanding Volunteer Award",
            'award_type_enum': AwardType.VOLUNTEER,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Mark Koors"}],
        }
        self.assertTrue(individual_award in awards)

    def test_parse_championship_divison_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012galileo.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 7)
        self.assertEqual(len(awards), 3)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Highest Rookie Seed - Galileo",
            'award_type_enum': AwardType.HIGHEST_ROOKIE_SEED,
            'team_number_list': [4394],
            'recipient_json_list': [{'team_number': 4394, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Championship Division Winners - Galileo",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [25, 180, 16],
            'recipient_json_list': [{'team_number': 25, 'awardee': None},
                                    {'team_number': 180, 'awardee': None},
                                    {'team_number': 16, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

    def test_parse_championship_2011(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2011cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 38)
        self.assertEqual(len(awards), 24)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Championship - Excellence in Design Award sponsored by Autodesk (3D CAD)",
            'award_type_enum': AwardType.EXCELLENCE_IN_DESIGN_CAD,
            'team_number_list': [75],
            'recipient_json_list': [{'team_number': 75, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

    def test_parse_championship_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 39)
        self.assertEqual(len(awards), 25)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Excellence in Design Award sponsored by Autodesk (3D CAD)",
            'award_type_enum': AwardType.EXCELLENCE_IN_DESIGN_CAD,
            'team_number_list': [862],
            'recipient_json_list': [{'team_number': 862, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        team_award = {
            'name_str': "Excellence in Design Award sponsored by Autodesk (Animation)",
            'award_type_enum': AwardType.EXCELLENCE_IN_DESIGN_ANIMATION,
            'team_number_list': [192],
            'recipient_json_list': [{'team_number': 192, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        team_award = {
            'name_str': "Entrepreneurship Award sponsored by Kleiner Perkins Caufield and Byers",
            'award_type_enum': AwardType.ENTREPRENEURSHIP,
            'team_number_list': [3132],
            'recipient_json_list': [{'team_number': 3132, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Founder's Award",
            'award_type_enum': AwardType.FOUNDERS,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Google"}],
        }
        self.assertTrue(individual_award in awards)

        # Test Multi Team and Individual Award
        multi_team_and_individual_award = {
            'name_str': "FIRST Dean's List Award",
            'award_type_enum': AwardType.DEANS_LIST,
            'team_number_list': [3059, 1540, 128, 1058, 3138, 3196, 1912, 2996, 842, 704],
            'recipient_json_list': [{'team_number': 3059, 'awardee': u"Ikechukwa Chima"},
                                    {'team_number': 1540, 'awardee': u"Marina Dimitrov"},
                                    {'team_number': 128, 'awardee': u"Chase Douglas"},
                                    {'team_number': 1058, 'awardee': u"Tristan Evarts"},
                                    {'team_number': 3138, 'awardee': u"Danielle Gehron"},
                                    {'team_number': 3196, 'awardee': u"David Gomez"},
                                    {'team_number': 1912, 'awardee': u"Rachel Holladay"},
                                    {'team_number': 2996, 'awardee': u"Jasmine Kemper"},
                                    {'team_number': 842, 'awardee': u"John Rangel"},
                                    {'team_number': 704, 'awardee': u"Matthew Ricks"}],
        }
        self.assertTrue(multi_team_and_individual_award in awards)

        # Test Team and Individual Award
        team_and_individual_award = {
            'name_str': "Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [2614],
            'recipient_json_list': [{'team_number': 2614, 'awardee': u"Earl Scime"}],
        }
        self.assertTrue(team_and_individual_award in awards)

    def test_parse_championship_2013(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2013cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 37)
        self.assertEqual(len(awards), 22)

        awards = convert_to_comparable(awards)

        # Test New Awards
        new_award = {
            'name_str': "Make It Loud Award",
            'award_type_enum': AwardType.MAKE_IT_LOUD,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': "will.i.am"}],
        }
        self.assertTrue(new_award in awards)

        new_award = {
            'name_str': "Media and Technology Award sponsored by Comcast",
            'award_type_enum': AwardType.MEDIA_AND_TECHNOLOGY,
            'team_number_list': [2283],
            'recipient_json_list': [{'team_number': 2283, 'awardee': None}],
        }
        self.assertTrue(new_award in awards)

        new_award = {
            'name_str': "Dr. Bart Kamen Memorial Scholarship",
            'award_type_enum': AwardType.BART_KAMEN_MEMORIAL,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': "Sofia Dhanani"},
                                    {'team_number': None, 'awardee': "Sarah Rudasill"},
                                    {'team_number': None, 'awardee': "Pascale Wallace Patterson"}],
        }
        self.assertTrue(new_award in awards)

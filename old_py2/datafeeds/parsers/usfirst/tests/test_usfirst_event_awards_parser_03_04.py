import unittest2
import json

from consts.award_type import AwardType
from datafeeds.usfirst_event_awards_parser_03_04 import UsfirstEventAwardsParser_03_04


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
class TestUsfirstEventAwardsParser_03_04(unittest2.TestCase):
    def test_parse_regional_2004(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2004sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_03_04.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 26)
        self.assertEqual(len(awards), 21)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': u"Regional Chairman\u2019s Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [254],
            'recipient_json_list': [{'team_number': 254, 'awardee': None}]
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [971, 254, 852],
            'recipient_json_list': [{'team_number': 971, 'awardee': None},
                                    {'team_number': 254, 'awardee': None},
                                    {'team_number': 852, 'awardee': None}]
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Regional Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [115],
            'recipient_json_list': [{'team_number': 115, 'awardee': u"Ted Shinta"}]
        }
        self.assertTrue(individual_award in awards)

    def test_parse_regional_2003(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2003sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_03_04.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 25)
        self.assertEqual(len(awards), 18)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': u"Regional Chairman\u2019s Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [359],
            'recipient_json_list': [{'team_number': 359, 'awardee': None}]
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [115, 254, 852],
            'recipient_json_list': [{'team_number': 115, 'awardee': None},
                                    {'team_number': 254, 'awardee': None},
                                    {'team_number': 852, 'awardee': None}]
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Silicon Valley Regional Volunteer of the Year",
            'award_type_enum': AwardType.VOLUNTEER,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"Ken Krieger"},
                                    {'team_number': None, 'awardee': u"Ken Leung"}]
        }
        self.assertTrue(individual_award in awards)

    def test_parse_cmp_2003(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2003cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_03_04.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 26)
        self.assertEqual(len(awards), 20)

        awards = convert_to_comparable(awards)

        team_award = {
            'name_str': u"Rookie All Star Award",
            'award_type_enum': AwardType.ROOKIE_ALL_STAR,
            'team_number_list': [1108, 1023],
            'recipient_json_list': [{'team_number': 1108, 'awardee': None},
                                    {'team_number': 1023, 'awardee': None}]
        }
        self.assertTrue(team_award in awards)

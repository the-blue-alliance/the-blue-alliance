import unittest2
import json

from consts.award_type import AwardType
from datafeeds.usfirst_event_awards_parser_05_06 import UsfirstEventAwardsParser_05_06


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
class TestUsfirstEventAwardsParser_05_06(unittest2.TestCase):
    def test_parse_regional_2006sj(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2006sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_05_06.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 27)
        self.assertEqual(len(awards), 22)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [192],
            'recipient_json_list': [{'team_number': 192, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [254, 581, 766],
            'recipient_json_list': [{'team_number': 254, 'awardee': None},
                                    {'team_number': 581, 'awardee': None},
                                    {'team_number': 766, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Regional Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [],
            'recipient_json_list': [{'team_number': None, 'awardee': u"William Dunbar"}],
        }
        self.assertTrue(individual_award in awards)

    def test_parse_regional_2006or(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2006or.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_05_06.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 28)
        self.assertEqual(len(awards), 22)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairman's Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [492],
            'recipient_json_list': [{'team_number': 492, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

    def test_parse_regional_2005sj(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2005sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_05_06.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 26)
        self.assertEqual(len(awards), 21)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': "Regional Chairmans Winner",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [368],
            'recipient_json_list': [{'team_number': 368, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [980, 254, 22],
            'recipient_json_list': [{'team_number': 980, 'awardee': None},
                                    {'team_number': 254, 'awardee': None},
                                    {'team_number': 22, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

        # Test Individual Award
        individual_award = {
            'name_str': "Regional Woodie Flowers Award",
            'award_type_enum': AwardType.WOODIE_FLOWERS,
            'team_number_list': [568],
            'recipient_json_list': [{'team_number': 568, 'awardee': u"AREA/BP/CIRI & Dimond High"}],
        }
        self.assertTrue(individual_award in awards)

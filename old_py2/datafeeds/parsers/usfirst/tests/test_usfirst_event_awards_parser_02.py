import unittest2
import json

from consts.award_type import AwardType
from datafeeds.usfirst_event_awards_parser_02 import UsfirstEventAwardsParser_02


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
class TestUsfirstEventAwardsParser_02(unittest2.TestCase):
    def test_parse_regional_2002(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2002sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser_02.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 26)
        self.assertEqual(len(awards), 20)

        awards = convert_to_comparable(awards)

        # Test Team Award
        team_award = {
            'name_str': u"Regional Chairmans Award",
            'award_type_enum': AwardType.CHAIRMANS,
            'team_number_list': [192],
            'recipient_json_list': [{'team_number': 192, 'awardee': None}],
        }
        self.assertTrue(team_award in awards)

        individual_award = {
            'name_str': "#1 Seed",
            'award_type_enum': AwardType.NUM_1_SEED,
            'team_number_list': [254],
            'recipient_json_list': [{'team_number': 254, 'awardee': None}],
        }
        self.assertTrue(individual_award in awards)

        # Test Multi Team Award
        multi_team_award = {
            'name_str': "Regional Winner",
            'award_type_enum': AwardType.WINNER,
            'team_number_list': [254, 60, 359],
            'recipient_json_list': [{'team_number': 254, 'awardee': None},
                                    {'team_number': 60, 'awardee': None},
                                    {'team_number': 359, 'awardee': None}],
        }
        self.assertTrue(multi_team_award in awards)

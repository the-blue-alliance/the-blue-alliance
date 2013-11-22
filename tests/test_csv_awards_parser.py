import unittest2
import json

from consts.award_type import AwardType
from datafeeds.csv_awards_parser import CSVAwardsParser


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


class TestCSVAwardssParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/pre_2002_regional_awards.csv', 'r') as f:
            awards = CSVAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 885)
        self.assertEqual(len(awards), 601)

        awards = convert_to_comparable(awards)

        award = {
            'year': 1995,
            'event_short': 'nh',
            'name_str': "Team Spirit Award",
            'award_type_enum': AwardType.SPIRIT,
            'team_number_list': [213],
            'recipient_json_list': [{'team_number': 213, 'awardee': None}],
        }
        self.assertTrue(award in awards)

        award = {
            'year': 2000,
            'event_short': 'mi',
            'name_str': "Best Offensive Round",
            'award_type_enum': AwardType.BEST_OFFENSIVE_ROUND,
            'team_number_list': [1, 240],
            'recipient_json_list': [{'team_number': 1, 'awardee': None},
                                    {'team_number': 240, 'awardee': None}],
        }
        self.assertTrue(award in awards)

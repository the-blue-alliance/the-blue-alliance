import unittest2
import json

from tba.consts.award_type import AwardType
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
    def test_parse_regional_awards(self):
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

    def test_parse_cmp_awards(self):
        with open('test_data/pre_2007_cmp_awards.csv', 'r') as f:
            awards = CSVAwardsParser.parse(f.read())

        # Check number of parsed awards
        num_awards = 0
        for award in awards:
            num_awards += len(award['recipient_json_list'])
        self.assertEqual(num_awards, 560)
        self.assertEqual(len(awards), 330)

        awards = convert_to_comparable(awards)

        award = {
            'year': 2003,
            'event_short': 'cmp',
            'name_str': "Championship Finalist",
            'award_type_enum': AwardType.FINALIST,
            'team_number_list': [25, 343, 494],
            'recipient_json_list': [{'team_number': 25, 'awardee': None},
                                    {'team_number': 343, 'awardee': None},
                                    {'team_number': 494, 'awardee': None}],
        }
        self.assertTrue(award in awards)

        award = {
            'year': 2002,
            'event_short': 'arc',
            'name_str': "#1 Seed",
            'award_type_enum': AwardType.NUM_1_SEED,
            'team_number_list': [121],
            'recipient_json_list': [{'team_number': 121, 'awardee': None}],
        }
        self.assertTrue(award in awards)

        award = {
            'year': 1992,
            'event_short': 'cmp',
            'name_str': "Play of the Day",
            'award_type_enum': AwardType.PLAY_OF_THE_DAY,
            'team_number_list': [131],
            'recipient_json_list': [{'team_number': 131, 'awardee': None}],
        }
        self.assertTrue(award in awards)

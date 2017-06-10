import csv
import json
import StringIO

from consts.award_type import AwardType
from datafeeds.parser_base import ParserBase
from helpers.award_helper import AwardHelper
from models.award import Award


class CSVAwardsParser(ParserBase):
    @classmethod
    def parse(cls, data):
        """
        Parse CSV that contains awards
        Format is as follows:
        year, event_short, award_name_str, team_number (can be blank), awardee (can be blank)
        Example:
        2000,mi,Regional Finalist,45,
        """
        awards_by_key = {}
        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for award in csv_data:
            year = int(award[0])
            event_short = award[1]
            name_str = award[2]
            team_number = award[3]
            awardee = award[4]

            if team_number == '':
                team_number = None
            else:
                team_number = int(team_number)
            if awardee == '':
                awardee = None
            # an award must have either an awardee or a team_number
            if awardee is None and team_number is None:
                continue

            if team_number is not None:
                team_number_list = [team_number]
            else:
                team_number_list = []

            recipient_json = json.dumps({
                'team_number': team_number,
                'awardee': awardee,
            })

            award_type_enum = AwardHelper.parse_award_type(name_str)
            if award_type_enum is None:
                # If we can't figure it out, fall back to OTHER (good for offseason events)
                award_type_enum = AwardType.OTHER
            award_key_name = Award.render_key_name('{}{}'.format(year, event_short), award_type_enum)

            if award_key_name in awards_by_key:
                if team_number is not None:
                    awards_by_key[award_key_name]['team_number_list'].append(team_number)
                awards_by_key[award_key_name]['recipient_json_list'].append(recipient_json)
            else:
                awards_by_key[award_key_name] = {
                    'year': year,
                    'event_short': event_short,
                    'name_str': name_str,
                    'award_type_enum': award_type_enum,
                    'team_number_list': team_number_list,
                    'recipient_json_list': [recipient_json],
                }
        return awards_by_key.values()

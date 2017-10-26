import json
import re

from datafeeds.parser_base import ParserInputException, ParserBase
from helpers.award_helper import AwardHelper
from models.award import Award


class JSONAwardsParser(ParserBase):
    @classmethod
    def parse(self, awards_json, event_key):
        """
        Parse JSON that contains a list of awards where each award is a dict of:
        name_str: String of award name. ex: "Tournament Winner" or "Dean's List Finalist"
        team_key: String in the format "frcXXX" for the team that won the award. Can be null.
        awardee: String corresponding to the name of an individual that won the award. Can be null.
        """
        try:
            awards = json.loads(awards_json)
        except:
            raise ParserInputException("Invalid JSON. Please check input.")

        awards_by_key = {}
        for award in awards:
            if type(award) is not dict:
                raise ParserInputException("Awards must be dicts.")

            name_str = award.get('name_str', None)
            team_key = award.get('team_key', None)
            awardee = award.get('awardee', None)

            if name_str is None:
                raise ParserInputException("Award must have a 'name_str'")

            if team_key and not re.match(r'frc\d+', str(team_key)):
                raise ParserInputException(
                    "Bad team_key: '{}'. Must follow format 'frcXXX' or be null.".
                    format(team_key))

            award_type_enum = AwardHelper.parse_award_type(name_str)
            if award_type_enum is None:
                raise ParserInputException(
                    "Cannot determine award type from: '{}'. Please contact a www.thebluealliance.com admin.".
                    format(name_str))

            recipient_json = json.dumps({
                'team_number':
                int(team_key[3:]) if team_key else None,
                'awardee':
                awardee,
            })

            award_key_name = Award.render_key_name(event_key, award_type_enum)
            if award_key_name in awards_by_key:
                if team_key is not None:
                    awards_by_key[award_key_name]['team_key_list'].append(
                        team_key)
                awards_by_key[award_key_name]['recipient_json_list'].append(
                    recipient_json)
            else:
                awards_by_key[award_key_name] = {
                    'name_str': name_str,
                    'award_type_enum': award_type_enum,
                    'team_key_list': [team_key] if team_key else [],
                    'recipient_json_list': [recipient_json],
                }

        return awards_by_key.values()

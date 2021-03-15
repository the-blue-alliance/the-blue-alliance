import json
import logging
import re

from bs4 import BeautifulSoup

from consts.award_type import AwardType
from datafeeds.parser_base import ParserBase
from helpers.award_helper import AwardHelper


class UsfirstEventAwardsParser_02(ParserBase):
    """
    Parses USFIRST event award pages for awards
    """

    @classmethod
    def parse(self, html):
        """
        Parse the awards from USFIRST.
        """
        html = html.decode('utf-8', 'ignore')  # Clean html before feeding itno BeautifulSoup
        soup = BeautifulSoup(html)
        table = soup.findAll('table')[6]

        awards_by_type = {}
        for tr in table.findAll('tr')[3:]:
            tds = tr.findAll('td')

            name_str = unicode(self._recurseUntilString(tds[0]))
            award_type_enum = AwardHelper.parse_award_type(name_str)
            if award_type_enum is None:
                continue

            team_number = None
            try:
                team_number = self._recurseUntilString(tds[1])
            except AttributeError:
                team_number = None
            if team_number and team_number.isdigit():
                team_number = int(team_number)
            else:
                team_number = None

            awardee = None
            if award_type_enum in AwardType.INDIVIDUAL_AWARDS:
                try:
                    awardee_str = self._recurseUntilString(tds[2])
                    if awardee_str:
                        awardee = unicode(sanitize(awardee_str))
                except TypeError:
                    awardee = None
                if not awardee:
                    # Turns '' into None
                    awardee = None

            # an award must have either an awardee or a team_number
            if awardee is None and team_number is None:
                continue

            recipient_json = json.dumps({
                'team_number': team_number,
                'awardee': awardee,
            })

            if award_type_enum in awards_by_type:
                if team_number is not None:
                    awards_by_type[award_type_enum]['team_number_list'].append(team_number)
                awards_by_type[award_type_enum]['recipient_json_list'].append(recipient_json)
            else:
                awards_by_type[award_type_enum] = {
                    'name_str': strip_number(name_str),
                    'award_type_enum': award_type_enum,
                    'team_number_list': [team_number] if team_number is not None else [],
                    'recipient_json_list': [recipient_json],
                }

        return awards_by_type.values(), False


def sanitize(text):
    return text.replace('\r\n ', '')


def strip_number(text):
    # Removes things like "3" from the end an award name_str
    # Example: "Regional Winner 3" becomes "Regional Winner"
    m = re.match(r'(.*)\d$', text)
    if m is not None:
        return m.group(1).strip()
    else:
        return text.strip()

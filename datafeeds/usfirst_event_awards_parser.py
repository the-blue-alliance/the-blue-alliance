import json
import logging
import re

from bs4 import BeautifulSoup

from consts.award_type import AwardType
from datafeeds.parser_base import ParserBase
from helpers.award_helper import AwardHelper


class UsfirstEventAwardsParser(ParserBase):
    """
    Parses USFIRST event award pages for awards
    Works for events 2007-present
    """
    # The format of USFIRST award pages is different for 2007-2011 and 2012-present
    # This dict defines which columns of the USFIRST award table name_str, team_number, and individual are.
    COL_NUM = {'2012-pres': {'name_str': 0,
                             'team_number': 1,
                             'individual': 3},
               '2007-11': {'name_str': 0,
                           'team_number': 1,
                           'individual': 2}}

    @classmethod
    def parse(self, html):
        """
        Parse the awards from USFIRST.
        """
        html = html.decode('utf-8', 'ignore')  # Clean html before feeding itno BeautifulSoup
        soup = BeautifulSoup(html)
        table = soup.findAll('table')[2]

        awards_by_type = {}
        for tr in table.findAll('tr')[1:]:
            tds = tr.findAll('td')
            if len(tds) == 5:
                parser_year = '2012-pres'
            else:
                parser_year = '2007-11'

            name_str = unicode(self._recurseUntilString(tds[self.COL_NUM[parser_year]['name_str']]))
            award_type_enum = AwardHelper.parse_award_type(name_str)
            if award_type_enum is None:
                continue

            team_number = None
            try:
                team_number = self._recurseUntilString(tds[self.COL_NUM[parser_year]['team_number']])
            except AttributeError:
                team_number = None
            if team_number and team_number.isdigit():
                team_number = int(team_number)
            else:
                team_number = None

            awardee = None
            if award_type_enum in AwardType.INDIVIDUAL_AWARDS:
                try:
                    awardee_str = self._recurseUntilString(tds[self.COL_NUM[parser_year]['individual']])
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
    # Removes things like "#3" from an award name_str
    # Example: "Regional Winners #2" becomes "Regional Winners"
    m = re.match(r'(.*) #\d*(.*)', text)
    if m is not None:
        return m.group(1) + m.group(2)
    else:
        return text

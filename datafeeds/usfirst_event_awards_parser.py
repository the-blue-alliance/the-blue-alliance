import json
import logging
import re

from BeautifulSoup import BeautifulSoup

from consts.award_type import AwardType
from datafeeds.parser_base import ParserBase


class UsfirstEventAwardsParser(ParserBase):
    """
    Works for official events from 2007-present
    Note: awards are matched by award names below, but the award names
    displayed will be the award names listed on the USFIRST event pages.
    Awards must contain every string in the the first list of the tuple
    and must NOT contain any string in the second list of the tuple
    """
    AWARD_NAMES = [
        (AwardType.CHAIRMANS, (["chairman"], [])),
        (AwardType.ENGINEERING_INSPIRATION, (["engineering inspiration"], [])),
        (AwardType.WINNER, (["winner", "1"], [])),
        (AwardType.WINNER, (["winner", "2"], [])),
        (AwardType.WINNER, (["winner", "3"], [])),
        (AwardType.WINNER, (["winner", "4"], [])),
        (AwardType.WINNER, (["championship", "champion", "1"], ["finalist"])),
        (AwardType.WINNER, (["championship", "champion", "2"], ["finalist"])),
        (AwardType.WINNER, (["championship", "champion", "3"], ["finalist"])),
        (AwardType.WINNER, (["championship", "champion", "4"], ["finalist"])),
        (AwardType.FINALIST, (["finalist", "1"], ["dean"])),
        (AwardType.FINALIST, (["finalist", "2"], ["dean"])),
        (AwardType.FINALIST, (["finalist", "3"], ["dean"])),
        (AwardType.FINALIST, (["finalist", "4"], ["dean"])),
        (AwardType.COOPERTITION, (["coopertition"], [])),
        (AwardType.SPORTSMANSHIP, (["sportsmanship"], [])),
        (AwardType.CREATIVITY, (["creativity"], [])),
        (AwardType.ENGINEERING_EXCELLENCE, (["engineering", "excellence"], [])),
        (AwardType.ENTREPRENEURSHIP, (["entrepreneurship"], [])),
        (AwardType.EXCELLENCE_IN_DESIGN, (["excellence in design"], ["cad", "animation"])),
        (AwardType.EXCELLENCE_IN_DESIGN_CAD, (["excellence in design", "cad"], [])),
        (AwardType.EXCELLENCE_IN_DESIGN_ANIMATION, (["excellence in design", "animation"], [])),
        (AwardType.DEANS_LIST, (["dean", "list"], [])),
        (AwardType.BART_KAMEN_MEMORIAL, (["bart", "kamen", "memorial"], [])),
        (AwardType.DRIVING_TOMORROWS_TECHNOLOGY, (["driving", "tomorrow", "technology"], [])),
        (AwardType.GRACIOUS_PROFESSIONALISM, (["gracious professionalism"], [])),
        (AwardType.HIGHEST_ROOKIE_SEED, (["highest rookie seed"], [])),
        (AwardType.IMAGERY, (["imagery"], [])),
        (AwardType.INDUSTRIAL_DEESIGN, (["industrial design"], [])),
        (AwardType.MEDIA_AND_TECHNOLOGY, (["media", "technology"], [])),
        (AwardType.MAKE_IT_LOUD, (["make", "loud"], [])),
        (AwardType.SAFETY, (["safety"], [])),
        (AwardType.INNOVATION_IN_CONTROL, (["innovation in control"], [])),
        (AwardType.QUALITY, (["quality"], [])),
        (AwardType.ROOKIE_ALL_STAR, (["rookie", "all", "star"], [])),
        (AwardType.ROOKIE_INSPIRATION, (["rookie inspiration"], [])),
        (AwardType.SPIRIT, (["spirit"], [])),
        (AwardType.WEBSITE, (["website"], [])),
        (AwardType.VISUALIZATION, (["visualization"], [])),
        (AwardType.VOLUNTEER, (["volunteer"], [])),
        (AwardType.WOODIE_FLOWERS, (["woodie flowers"], [])),
        (AwardType.JUDGES, (["judge"], [])),
        (AwardType.FOUNDERS, (["founder"], [])),
        (AwardType.AUTODESK_INVENTOR, (["autodesk inventor"], [])),
        (AwardType.FUTURE_INNOVATOR, (["future innovator"], []))
    ]
    YEAR_SPECIFIC = {'2012-pres': {'name_str': 0,
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
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        table = soup.findAll('table')[2]

        awards_by_type = {}
        for tr in table.findAll('tr')[1:]:
            tds = tr.findAll('td')
            if len(tds) == 5:
                year = '2012-pres'
            else:
                year = '2007-11'

            name_str = unicode(self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['name_str']]))
            name_str_lower = name_str.lower()
            award_type_enum = None
            for type_enum, (yes_strings, no_strings) in self.AWARD_NAMES:
                for string in yes_strings:
                    if string not in name_str_lower:
                        break
                else:
                    for string in no_strings:
                        if string in name_str_lower:
                            break
                    else:
                        # found a match
                        award_type_enum = type_enum
                        break
            if award_type_enum is None:
                logging.warning("Found an award without an associated type: " + name_str)
                continue

            team_number = None
            try:
                team_number = self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['team_number']])
            except AttributeError:
                team_number = None
            if team_number and team_number.isdigit():
                team_number = int(team_number)
            else:
                team_number = None

            awardee = None
            if award_type_enum in AwardType.INDIVIDUAL_AWARDS:
                try:
                    awardee_str = self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['individual']])
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

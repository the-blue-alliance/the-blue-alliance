import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class UsfirstEventAwardsParser(ParserBase):
    """
    Works for official events from 2007-2012
    Note: awards are matched by award names below, but the award names
    displayed will be the award names listed on the USFIRST event pages.
    Awards must contain every string in the the first list of the tuple
    and must NOT contain any string in the second list of the tuple
    """
    AWARD_NAMES = {   
        "ca": (["chairman"], []),
        "ei": (["engineering inspiration"], []),
        "win1": (["winner", "1"], []),
        "win2": (["winner", "2"], []),
        "win3": (["winner", "3"], []),
        "win4": (["winner", "4"], []),
        "fin1": (["finalist", "1"], ["dean"]),
        "fin2": (["finalist", "2"], ["dean"]),
        "fin3": (["finalist", "3"], ["dean"]),
        "fin4": (["finalist", "4"], ["dean"]),
        "coop": (["coopertition"], []),
        "sports": (["sportsmanship"], []),
        "create": (["creativity"], []),
        "eng": (["engineering excellence"], []),
        "entre": (["entrepreneurship"], []),
        "exdes": (["excellence in design"], []),
        "dl": (["dean's list"], []),
        "driv": (["driving", "tomorrow", "technology"], []),
        "gp": (["gracious professionalism"], []),
        "hrs": (["highest rookie seed"], []),
        "image": (["imagery"], []),
        "ind": (["industrial design"], []),
        "safe": (["safety"], []),
        "control": (["innovation in control"], []),
        "quality": (["quality"], []),
        "ras": (["rookie", "all", "star"], []),
        "rinspire": (["rookie inspiration"], []),
        "spirit": (["spirit"], []),
        "web": (["website"], []),
        "vis": (["visualization"], []),
        "vol": (["volunteer"], []),
        "wfa": (["woodie flowers"], []),
        "judge": (["judge"], []),
        "founders": (["founder"], []),
        "inventor": (["autodesk inventor"], []),
        "innovator": (["future innovator"], []),
    }
    INDIVIDUAL_AWARDS = ["dl", "dl1", "dl2", "dl3", "dl4", "dl5", "dl6", "dl7", "dl8", "dl9", "vol", "wfa", "founders"]    
    YEAR_SPECIFIC = {'2012': {'official': 0,
                              'team_number': 1,
                              'individual': 3},
                     '2007-11': {'official': 0,
                                 'team_number': 1,
                                 'individual': 2}}
    
    @classmethod    
    def parse(self, html):
        """
        Parse the awards from USFIRST.
        """
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)

        title = self._recurseUntilString(soup.findAll('title')[0])
        
        is_championship = title.find('FIRST Championship') >= 0
        if is_championship and title.find('Division') >= 0:
            is_division = True
        else:
            is_division = False

        table = soup.findAll('table')[2]
        already_parsed = set()
        awards = list()
        for tr in table.findAll('tr')[1:]:
            tds = tr.findAll('td')
            if len(tds) == 5:
                year = '2012'
            else:
                year = '2007-11'

            official_name = unicode(self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['official']]))
            award_key = None
            official_name_lower = official_name.lower()
            for key, (yes_strings, no_strings) in self.AWARD_NAMES.items():
                for string in yes_strings:
                    if string not in official_name_lower:
                        break
                else:
                    for string in no_strings:
                        if string in official_name_lower:
                            break
                    else:
                        award_key = key
                        break
            if not award_key:
                logging.warning('Found an award that isn\'t in the dictionary: ' + official_name)
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
            if award_key in self.INDIVIDUAL_AWARDS:
                try:
                    awardee = fixAwardee(tds[self.YEAR_SPECIFIC[year]['individual']])
                    if awardee:
                        awardee = unicode(sanitize(awardee))
                except TypeError:
                    awardee = None
                if not awardee:
                    # Turns '' into None
                    awardee = None

            if (awardee == None) and (team_number == None):
                continue

            key_number = 1
            test_key = award_key
            while test_key in already_parsed:
                test_key = award_key + str(key_number)
                key_number += 1
            award_key = test_key
            already_parsed.add(award_key)
            
            if is_championship:
                if is_division:
                    award_key = 'div_' + award_key
                else:
                    award_key = 'cmp_' + award_key
                    
            award = {'name': award_key,
                     'team_number': team_number,
                     'awardee': awardee,
                     'official_name': official_name}
            awards.append(award)
        return awards

def fixAwardee(text):
    # Example: http://www2.usfirst.org/2012comp/Events/gl/awards.html
    # Some names have <span></span> around names, but not others.
    spans = text.findAll('span')
    if not spans:
        return ParserBase._recurseUntilString(text)
    full_name = []
    for span in spans:
        try:
            partial = ParserBase._recurseUntilString(span)
            if partial not in full_name:
                full_name.append(partial)
        except AttributeError:
            continue
    return ' '.join(full_name)

def sanitize(text):
    return text.replace('\r\n ', '')

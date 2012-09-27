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
        "rca": (["chairman"], []),
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
        "create": (["creativity"], []),
        "eng": (["engineering excellence"], []),
        "entre": (["entrepreneurship"], []),
        "exdes": (["excellence in design"], []),
        "dlf1": (["dean's list finalist", "1"], []),
        "dlf2": (["dean's list finalist", "2"], []),
        "dlf3": (["dean's list finalist", "3"], []),
        "dlf4": (["dean's list finalist", "4"], []),
        "dlf5": (["dean's list finalist", "5"], []),
        "dlf6": (["dean's list finalist", "6"], []),
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
    }
    INDIVIDUAL_AWARDS = ["dlf1", "dlf2", "dlf3", "dlf4", "dlf5", "dlf6", "vol", "wfa"]    
    NO_TEAM_AWARDS = ["vol"] #awards which don't have to be associated with a team
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
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)

        table = soup.findAll('table')[2]
        already_parsed = set()
        awards = list()
        for tr in table.findAll('tr')[1:]:
            tds = tr.findAll('td')
            if len(tds) == 5:
                year = '2012'
            else:
                year = '2007-11'

            official_name = str(self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['official']]))
            try:
                team_number = int(self._recurseUntilString(tds[self.YEAR_SPECIFIC[year]['team_number']]))
            except AttributeError:
                team_number = 0
            except ValueError:
                team_number = 0
            except TypeError:
                team_number = 0
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
                #award doesn't exist?
                logging.error('Found an award that isn\'t in the dictionary: ' + official_name)
                continue #silently ignore
            if (not award_key in self.NO_TEAM_AWARDS) and (team_number == 0):
                #award doesn't have a team set, probably wasn't given
                continue #skip
            if award_key in self.INDIVIDUAL_AWARDS:
                try:
                    awardee = fixAwardee(tds[self.YEAR_SPECIFIC[year]['individual']])
                    awardee = sanitize(awardee)
                except TypeError:
                    #they didn't award it but still listed it?
                    continue
                if not awardee:
                    #they didn't award it but still listed it?
                    continue
            else:
                awardee = ''

            key_number = 1
            while award_key in already_parsed:
                award_key += unicode(key_number)
                key_number += 1
            award = {'name': award_key,
                     'team_number': team_number,
                     'awardee': unicode(awardee),
                     'official_name': unicode(official_name)}
            awards.append(award)
            already_parsed.add(award_key)
        return awards

def fixAwardee(text):
    # Fix funny formatting with USFIRST's awards page
    spans = text.findAll('span')
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

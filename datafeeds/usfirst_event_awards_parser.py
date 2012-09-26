import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class UsfirstEventAwardsParser(ParserBase):
    """
    Works for official events from 2012
    """
    AWARD_NAMES = {
        "rca": ["Regional Chairman's Award"],
        "ei": ["Engineering Inspiration Award"],
        "win1": ["Regional Winners #1"],
        "win2": ["Regional Winners #2"],
        "win3": ["Regional Winners #3"],
        "win4": ["Regional Winners #4"],

        "fin1": ["Regional Finalists #1"],
        "fin2": ["Regional Finalists #2"],
        "fin3": ["Regional Finalists #3"],
        "fin4": ["Regional Finalists #4"],
        "coop": ["Coopertition Award"],
        "create": ["Creativity Award sponsored by Xerox"],
        "eng": ["Engineering Excellence Award sponsored by Delphi"],
        "entre": ["Entrepreneurship Award sponsored by Kleiner Perkins Caufield and Byers"],
        "dlf": ["FIRST Dean's List Finalist Award #1"],
        "dlf2": ["FIRST Dean's List Finalist Award #2"],
        "dlf3": ["FIRST Dean's List Finalist Award #3"],
        "dlf4": ["FIRST Dean's List Finalist Award #4"],
        "dlf5": ["FIRST Dean's List Finalist Award #5"],
        "dlf6": ["FIRST Dean's List Finalist Award #6"],
        "gp": ["Gracious Professionalism Award sponsored by Johnson & Johnson"],
        "hrs": ["Highest Rookie Seed"],
        "image": ["Imagery Award in honor of Jack Kamen"],
        "ind": ["Industrial Design Award sponsored by General Motors"],
        "safe": ["Industrial Safety Award sponsored by Underwriters Laboratories"],
        "control": ["Innovation in Control Award sponsored by Rockwell Automation"],
        "quality": ["Quality Award sponsored by Motorola"],
        "ras": ["Rookie All Star Award"],
        "rinspire": ["Rookie Inspiration Award"],
        "spirit": ["Team Spirit Award sponsored by Chrysler"],
        "web": ["Website Award"],
        "vol": ["Volunteer of the Year"],
        "wfa": ["Woodie Flowers Finalist Award"],
        "judge": ["Judges' Award #1"],
        "judge2": ["Judges' Award #2"],
    }
    INDIVIDUAL_AWARDS = ["dlf", "dlf2", "dlf3", "dlf4", "dlf5", "dlf6", "vol", "wfa"]    
    NO_TEAM_AWARDS = ["vol"] #awards which don't have to be associated with a team    
    
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
            official_name = str(self._recurseUntilString(tds[0]))
            try:
                team_number = int(self._recurseUntilString(tds[1]))
            except AttributeError:
                team_number = 0
            except ValueError:
                team_number = 0
            award_key = None
            for key in self.AWARD_NAMES:
                if official_name in self.AWARD_NAMES[key]:
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
                    awardee = str(self._recurseUntilString(tds[3]))
                except TypeError:
                    #they didn't award it but still listed it?
                    continue
            else:
                awardee = ''
            key_number = 1
            while award_key in already_parsed:
                award_key += unicode(key_number)
                key_number += 1
            award = {'name': award_key,
                     'winner': team_number,
                     'awardee': unicode(awardee),
                     'official_name': unicode(official_name)}
            awards.append(award)
            already_parsed.add(award_key)
        return awards

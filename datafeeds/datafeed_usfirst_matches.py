import logging
import re
from datetime import datetime

from google.appengine.api import urlfetch
from google.appengine.ext import db

from django.utils import simplejson

from BeautifulSoup import BeautifulSoup, NavigableString

from models import Match

class DatafeedUsfirstMatches(object):
    """
    Facilitates grabbing Match information from USFIRST.org. It enables
    discovering matches from official FIRST events. 
    It returns Match model objects, but does no database IO itself.
    """
    
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
    }
    
    MATCH_RESULTS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/matchresults.html" # % (year, event_short)
    MATCH_SCHEDULE_QUAL_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/schedulequal.html"
    MATCH_SCHEDULE_ELIMS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/scheduleelim.html"
    
    def getKeyName(self, event, comp_level, set_number, match_number):
        event_part = str(event.year) + str(event.event_short)
        if comp_level == "qm":
            match_part = comp_level + str(match_number)
        else:
            match_part = comp_level + str(set_number) + "m" + str(match_number)
        return event_part + "_" + match_part
    
    def getMatchResultsList(self, event):
        """
        Return a list of Matches based on the FIRST match results page.
        """
        
        url = self.MATCH_RESULTS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return self.parseMatchResultsList(event, result.content)
        else:
            logging.error('Unable to retreive url: ' + url)
    
    
    def parseMatchResultsList(self, event, html):
        """
        Parse the match results from USFIRST. This provides us
        with information about Matches and the teams that played in them.
        Match exists in the database. (??? Really? -greg)
        {"match": Match, "teams": {"red": list(), "blue": list()}, "scores": {"red": int, "blue": int}}
        """
        matches = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        tables = soup.findAll('table')
        
        matches.extend(self.parseQualMatchResultList(event, tables[2]))
        matches.extend(self.parseElimMatchResultList(event, tables[2]))
        matches.extend(self.parseElimMatchResultList(event, tables[3]))
        
        return matches
    
    def parseQualMatchResultList(self, event, table):
        """
        Parse the table that contains qualification match results.
        """
        matches = list()
        
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 10:
                if self._recurseUntilString(tds[1]) is not None:
                    red_teams = ["frc" + self._recurseUntilString(tds[2]), "frc" + self._recurseUntilString(tds[3]), "frc" + self._recurseUntilString(tds[4])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[5]), "frc" + self._recurseUntilString(tds[6]), "frc" + self._recurseUntilString(tds[7])]
                    
                    try:
                        if tds[8].string == None:
                            red_score = -1
                        else:
                            red_score = int(self._recurseUntilString(tds[8]))
                    
                        if tds[9].string == None:
                            blue_score = -1
                        else:
                            blue_score = int(self._recurseUntilString(tds[9]))
                        
                        comp_level = "qm"
                        set_number = 1
                        match_number = int(self._recurseUntilString(tds[1]))
                        
                        alliances = {
                            "red": {
                                "teams": red_teams,
                                "score": red_score
                            },
                            "blue": {
                                "teams": blue_teams,
                                "score": blue_score
                            }
                        }
                        
                        
                        match = Match(
                            key_name = self.getKeyName(event, "qm", 1, match_number),
                            event = event.key(),
                            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
                            set_number = 1,
                            match_number = match_number,
                            comp_level = "qm",
                            team_key_names = red_teams + blue_teams,
                            alliances_json = simplejson.dumps(alliances)
                        )
                        
                        matches.append(match)
                        
                    except Exception, detail:
                        logging.warning('Match Parse Failed: ' + str(detail))
                    
        return matches
    
    def parseElimMatchResultList(self, event, table):
        """
        Parse the table that contains elimination match results.
        """
        matches = list()
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 11:
                if self._recurseUntilString(tds[1]) is not None:
                    red_teams = ["frc" + self._recurseUntilString(tds[3]), "frc" + self._recurseUntilString(tds[4]), "frc" + self._recurseUntilString(tds[5])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[6]), "frc" + self._recurseUntilString(tds[7]), "frc" + self._recurseUntilString(tds[8])]
                    
                    try:
                        if self._recurseUntilString(tds[9]) == None:
                            red_score = -1
                        else:
                            red_score = int(self._recurseUntilString(tds[9]))
                        
                        if self._recurseUntilString(tds[10]) == None:
                            blue_score = -1
                        else:
                            blue_score = int(self._recurseUntilString(tds[10]))
                        
                        match_number_info = self.parseElimMatchNumberInfo(self._recurseUntilString(tds[1]))
                        
                        alliances = {
                            "red": {
                                "teams": red_teams,
                                "score": red_score
                            },
                            "blue": {
                                "teams": blue_teams,
                                "score": blue_score
                            }
                        }
                        
                        match = Match(
                            key_name = self.getKeyName(event, match_number_info["comp_level"], match_number_info["set_number"], match_number_info["match_number"]),
                            event = event.key(),
                            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
                            set_number = match_number_info["set_number"],
                            match_number = match_number_info["match_number"],
                            comp_level = match_number_info["comp_level"],
                            team_key_names = red_teams + blue_teams,
                            alliances_json = simplejson.dumps(alliances)
                        )
                        
                        # Don't write down uncompleted elimination matches
                        if (red_score > -1 and blue_score > -1):
                            matches.append(match)
                        
                    except Exception, detail:
                        logging.warning('Match Parse Failed: ' + str(detail))
        
        return matches
    
    
    def parseElimMatchNumberInfo(self, string):
        """
        Parse out the information about an elimination match based on the
        string USFIRST provides.
        They look like "Semi 2-2"
        """
        comp_level_dict = {
            "Qtr": "qf",
            "Semi": "sf",
            "Final": "f",
        }
        
        #string comes in as unicode.
        string = str(string)
        string = string.strip()
        
        match_number = int(string[-1:])
        set_number = int(string[-3:-2])
        comp_level = comp_level_dict[string[:-4]]
        
        results = {
            "match_number": match_number,
            "set_number": set_number,
            "comp_level": comp_level,
        }
        
        return results

    def _recurseUntilString(self, node):
        """
        Digs through HTML that Word made worse.
        Written to deal with http://www2.usfirst.org/2011comp/Events/cmp/matchresults.html
        """
        if node.string is not None:
            return node.string
        if isinstance(node, NavigableString):
            return node
        if hasattr(node, 'contents'):
            for content in node.contents:
                result = self._recurseUntilString(content)
                result = result.strip().replace('\r', '').replace('\n', '').replace('  ', ' ')
                if result is not None and result != "":
                    return result
        return None
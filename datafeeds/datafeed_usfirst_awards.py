import json
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from models import Award

class DatafeedUsfirstAwards(object):
    """
    Facilitates grabbing Award information from USFIRST.org. It enables
    discovering awards from official FIRST events. 
    It returns Award model objects, but does no database IO itself.
    """
    
    EVENT_SHORT_EXCEPTIONS = {
        "arc": "Archimedes",
        "cur": "Curie",
        "gal": "Galileo",
        "new": "Newton",
    }
    AWARD_NAMES = {
        "rca": ["Regional Chairman's Award"]
        "ei": ["Engineering Inspriation Award"]
        "win1": ["Regional Winners #1"]
        "win2": ["Regional Winners #2"]
        "win3": ["Regional Winners #3"]
        "fin1": ["Regional Finalists #1"]
        "fin2": ["Regional Finalists #2"]
        "fin3": ["Regional Finalists #3"]
        "coop": ["Coopertition Award"]
        "create": ["Creativity Award sponsored by Xerox"] 
        "eng": ["Engineering Excellence Award sponsored by Delphi"]
        "entre": ["Entrepreneurship Award sponsored by Kleiner Perkins Caufield and Byers"]
        "dlf": ["Dean's List Finalist #1"]
        "dlf2": ["Dean's List Finalist #2"]
        "gp": ["Gracious Professionalism Award sponsored by Johnson & Johnson"]
        "hrs": ["Highest Rookie Seed"]
        "image": ["Imagery Award in honor of Jack Kamen"]
        "ind": ["Industrial Design Award sponsored by General Motors"]
        "safe": ["Industrial Safety Award sponsored by Underwriters Laboratories"]
        "control": ["Innovation in Control Award sponsored by Rockwell Automation"]
        "quality": ["Quality Award sponsored by Motorola"]
        "ras": ["Rookie All Star Award"]
        "rinspire": ["Rookie Inspiration Award"]
        "spirit": ["Team Spirit Award sponsored by Chrysler"]
        "web": ["Website Award"]
        "vol": ["Volunteer of the Year"]
        "wfa": ["Woodie Flowers Finalist Award"]
        "judge": ["Judges' Award #1"]
        "judge2": ["Judges' Award #2"]
    }
    INDIVIDUAL_AWARDS = ["dlf", "dlf2", "vol", "wfa"]    
        
    
    AWARDS_URL_PATTERN = "http://www2.usfirst.org/%scomp/events/%s/awards.html" # % (year, event_short)
    
    
    def getAwardResultsList(self, event):
        """
        Return a list of Awards based on the FIRST award results page.
        """
        
        url = self.AWARDS_URL_PATTERN % (event.year,
            self.EVENT_SHORT_EXCEPTIONS.get(event.event_short, event.event_short))
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return self.parseAwardsResultsList(event, result.content)
        else:
            logging.error('Unable to retreive url: ' + url)
    
    def parseAwardResultsList(self, event, html):
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        table = soup.findAll('table')[2]
        awards = list()
        for tr in table.findAll('tr')[1:]:
            award_name = tr[0].p.span.contents[0]
            team_number = tr[1].p.span.contents[0]
            award_key = None
            for key in self.AWARD_NAMES:
                if award_name in self.AWARD_NAMES[key]:
                  award_key = key
                  break
            if not award_key:
                #award doesn't exist?
                logging.error('Found an award that isn\'t in the dictionary: ' + award_name)
            if award_key in self.INDIVIDUAL_AWARDS:
                awardee = tr[3].p.span.contents[0]
            else:
                awardee = ''
            object = Award(name = award_key, winner = team_number, awardee = awardee, year = event.year)
            awards.append(object)
        return awards

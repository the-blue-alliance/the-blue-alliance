import json
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from models.award import Award

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
    
    def sanitize(self, text):
        #because for some reason the first website is dumb
        #see http://www2.usfirst.org/2012comp/Events/gl/awards.html for an example
        return text.replace('\r\n ', '')
    
    def fixAwardee(self, text):
        #because for some reason the first website is dumb
        if len(text) != 2:
            return text.span.contents[0]
        spans = text.findAll('span')
        try:
            f_name = spans[1].contents[0]
            l_name = spans[3].contents[0]
        except:
            return text.span.contents[0]
        return f_name + ' ' + l_name
    
    def parseAwardsResultsList(self, event, html):
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        table = soup.findAll('table')[2]
        already_parsed = list()
        awards = list()
        for tr in table.findAll('tr')[1:]:
            tds = tr.findAll('td')
            official_name = self.sanitize(tds[0].p.span.contents[0])
            try:
                team_number = tds[1].p.span.contents[0]
            except AttributeError:
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
            if award_key in self.INDIVIDUAL_AWARDS:
                try:
                    awardee = self.fixAwardee(tds[3].p)
                except TypeError:
                    #they didn't award it but still listed it?
                    continue
            else:
                awardee = ''
            awardee = self.sanitize(awardee)
            try:
                team_number = int(str(team_number))
            except ValueError:
                team_number = 0
            key_number = 1
            while award_key in already_parsed:
                award_key += str(key_number)
                key_number += 1
            object = Award(
                name = award_key,
                winner = team_number,
                awardee = unicode(awardee),
                year = event.year,
                official_name = str(official_name),
                event = event,
            )
            awards.append(object)
            already_parsed.append(award_key)
        return awards

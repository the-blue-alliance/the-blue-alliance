import logging
import re

from google.appengine.api import urlfetch
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from helpers.team_helper import TeamTpidHelper

from models import Team


class DatafeedUsfirstTeams(object):
    """
    Facilitates getting information about Teams from USFIRST.
    """
    
    TEAM_DETAILS_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=team_details&tpid=%s&-session=myarea:%s"
    IMPOSSIBLY_HIGH_TEAM_NUMBER = 9999
    
    SESSION_KEY_GENERATING_URL = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&omit_searchform=1&season_FRC=%s"
    # It appears the Season we retreive from impacts the session key's working or not. 
    # "2010" keys did not work. -gregmarra 5 Dec 2010
    
    def getSessionKey(self, year=2011):
        """
        Grab a page from FIRST so we can get a session key out of URLs on it. This session
        key is needed to construct working event detail information URLs.
        """
        sessionRe = re.compile(r'myarea:([A-Za-z0-9]*)')
        
        result = urlfetch.fetch(self.SESSION_KEY_GENERATING_URL % year)
        if result.status_code == 200:
            regex_results = re.search(sessionRe, result.content)
            if regex_results is not None:
                session_key = regex_results.group(1) #first parenthetical group
                if session_key is not None:
                    return session_key
            logging.error('Unable to get USFIRST session key.')
            return None
        else:
            logging.error('Unable to retreive url: ' + self.SESSION_KEY_GENERATING_URL)
    
    def instantiateTeams(self, skip=0, year=2011):
        """
        Calling this function once establishes all of the Team objects in the Datastore.
        It does this by calling up USFIRST to search for Tpids. We have to do this in
        waves to avoid going over the GAE timeout.
        """
        
        #TeamTpidHelper actually creates Team objects.
        TeamTpidHelper.scrapeTpid(self.IMPOSSIBLY_HIGH_TEAM_NUMBER, skip, year)
    
    
    def flushTeams(self):
        """
        Delete Teams from the datastore. May take a few calls.
        NOTE: This breaks all relations such as EventTeams and Alliances.
        NEVER CALL THIS FUNCTION UNLESS YOU ARE ABSOLUTELY SERIOUS.
        """
        
        #TODO: This doesn't belong here. Move it to Controller? -gregmarra 7/31/2010
        
        teams = Team.all().fetch(500) #500 is max delete at once limit.
        db.delete(teams)
        
        
    def getTeamDetails(self, team_number):
        """
        Return a Team object for the requested team_number
        """
        
        team = Team.all().filter('team_number =', team_number).get()
        
        if team.first_tpid is not None:
            session_key = self.getSessionKey(team.first_tpid_year)
            url = self.TEAM_DETAILS_URL_PATTERN % (team.first_tpid, session_key)
            logging.info("Fetch url: %s" % url)
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                return self.parseTeamDetails(result.content)
            else:
                logging.error('Unable to retreive url: %s' % url)
                return None
        else:
            logging.error('Do not know Tpid for team %s' % team_number)
            return None
    
    def parseTeamDetails(self, html):
        """
        Parse the information table on USFIRSTs site to extract relevant team
        information. Return a Team object.
        """
        team_info = dict()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for tr in soup.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                field = str(tds[0].string)
                if field == "Team Number":
                    team_info["number"] = int(tds[1].b.string)
                if field == "Team Name":
                    team_info["name"] = unicode(self.smart_truncate(tds[1].string, 450))
                if field == "Team Location":
                    #TODO: Filter out &nbsp;'s and stuff -greg 5/21/2010
                    team_info["address"] = unicode(tds[1].string)
                #if field == "Rookie Season": #Unused
                #    team_info["rookie_season"] = int(tds[1].string)
                if field == "Team Nickname":
                    team_info["nickname"] = unicode(tds[1].string)
                if field == "Team Website":
                    try:
                        team_info["website"] = db.Link(unicode(tds[1].a["href"]))
                    except Exception, details:
                        logging.info("Team website is invalid for team %s." % team_info["number"])
        try:
            team = Team(
                team_number = team_info["number"],
                name = team_info.get("name", None),
                address = team_info.get("address", None),
                nickname = team_info.get("nickname", None),
                website = team_info.get("website", None)
            )        
            return team
        
        except Exception, e:
            logging.error("Team parsing failed. %s" % e)
            logging.info(soup.findAll('tr'))
            return None
  
    def smart_truncate(self, content, length=100, suffix='...'):
        # from http://stackoverflow.com/questions/250357/smart-truncate-in-python
        if len(content) <= length:
            return content
        else:
            return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix
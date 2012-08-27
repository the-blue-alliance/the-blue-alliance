import logging

# for db.link
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class UsfirstTeamDetailsParser(ParserBase):
    """
    Facilitates building TBAVideos store from TBA.
    """
    @classmethod
    def parse(self, html):
        """
        Parse the information table on USFIRSTs site to extract relevant team
        information. Return a dictionary.
        """
        team = dict()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        if soup.find(text='No team found.') is not None:
            logging.error('FIRST lacks team.')
            return None
        
        for tr in soup.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) > 1:
                field = str(tds[0].string)
                if field == "Team Number":
                    team["team_number"] = int(tds[1].b.string)
                if field == "Team Name":
                    team["name"] = unicode(tds[1].string)
                if field == "Team Location":
                    #TODO: Filter out &nbsp;'s and stuff -greg 5/21/2010
                    team["address"] = unicode(tds[1].string)
                #if field == "Rookie Season": #Unused
                #    team["rookie_season"] = int(tds[1].string)
                if field == "Team Nickname":
                    team["nickname"] = unicode(tds[1].string)
                if field == "Team Website":
                    try:
                        team["website"] = db.Link(unicode(tds[1].a["href"]))
                    except Exception, details:
                        logging.info("Team website is invalid for team %s." % team["team_number"])
        return team
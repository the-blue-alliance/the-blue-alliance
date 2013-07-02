import logging
import re

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
        
        page_title = soup.find('h1', {'id': 'thepagetitle'}).text
        team['team_number'] = int(re.search(r'Team Number ([0-9]+) \-', page_title).group(1).strip())
        team['nickname'] = unicode(re.search(r'"(.*)\"', page_title).group(1).strip())
        
        team['address'] = unicode(soup.find('div', {'class': 'team-address'}).find('div', {'class': 'content'}).text)
        
        team['name'] = unicode(soup.find('div', {'class': 'team-name'}).text)
        
        try:
            team['website'] = db.Link(unicode(soup.find('div', {'class': 'team-website'}).find('a')['href']))
        except Exception, details:
            logging.info("Team website is invalid for team %s." % team['team_number'])        
        
        return team, False

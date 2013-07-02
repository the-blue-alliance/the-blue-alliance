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
        # page_titles look like this:
        # Team Number <NUM> - "<NICK>"
        team_num_re = r'Team Number ([0-9]+) \-'
        team_nick_re = r'"(.*)\"'
        
        team = dict()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        page_title = soup.find('h1', {'id': 'thepagetitle'}).text
        team['team_number'] = int(re.search(team_num_re, page_title).group(1).strip())
        team['nickname'] = unicode(re.search(team_nick_re, page_title).group(1).strip())
        
        team['address'] = unicode(soup.find('div', {'class': 'team-address'}).find('div', {'class': 'content'}).text)
        
        team['name'] = unicode(soup.find('div', {'class': 'team-name'}).text)
        
        try:
            team['website'] = db.Link(unicode(soup.find('div', {'class': 'team-website'}).find('a')['href']))
        except Exception, details:
            logging.info("Team website is invalid for team %s." % team['team_number'])        
        
        return team, False

import logging
import re

# for db.link
from google.appengine.ext import db

from bs4 import BeautifulSoup

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

        # team addresses look like tihs:
        # <locality>, <region> <random string can have spaces> <country>
        team_address_re = r'(.*?), ([^ ]*) *.* (.*)'

        team = dict()
        soup = BeautifulSoup(html)

        page_title = soup.find('h1', {'id': 'thepagetitle'}).text
        try:
            team['team_number'] = int(re.search(team_num_re, page_title).group(1).strip())
        except AttributeError, details:
            logging.warning("Team number could not be parsed: {}".format(details))
            return None, False
        team['nickname'] = re.sub(' +', ' ', unicode(re.search(team_nick_re, page_title).group(1).strip()))

        full_address = unicode(soup.find('div', {'class': 'team-address'}).find('div', {'class': 'content'}).text)
        match = re.match(team_address_re, full_address)
        if match:
            locality, region, country = match.group(1), match.group(2), match.group(3)
            team['address'] = '%s, %s, %s' % (locality, region, country)

        team['name'] = unicode(soup.find('div', {'class': 'team-name'}).text)

        try:
            website_str = re.sub(r'^/|/$', '', unicode(soup.find('div', {'class': 'team-website'}).find('a')['href']))  # strip starting and trailing slashes
            if not (website_str.startswith('http://') or website_str.startswith('https://')):
                website_str = 'http://%s' % website_str
            team['website'] = db.Link(website_str)
        except Exception, details:
            logging.info("Team website is invalid for team %s." % team['team_number'])
            logging.info(details)

        self._html_unescape_items(team)

        return team, False

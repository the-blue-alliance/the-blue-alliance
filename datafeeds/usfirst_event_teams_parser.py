import re

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase

class UsfirstEventTeamsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Find what Teams are attending an Event, and return their team_numbers.
        """
        
        teamRe = re.compile(r'whats-going-on/team/FRC/[A-Za-z0-9=&;\-:]*?">\d+')
        teamNumberRe = re.compile(r'\d+$')
        tpidRe = re.compile(r'\d+')
        
        teams = list()   
        for teamResult in teamRe.findall(html):
            team = dict()
            team["team_number"] = int(teamNumberRe.findall(teamResult)[0])
            team["first_tpid"] = int(tpidRe.findall(teamResult)[0])
            teams.append(team)
        
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        more_pages = soup.find('a', {'title': 'Go to next page'}) is not None
        return teams, more_pages

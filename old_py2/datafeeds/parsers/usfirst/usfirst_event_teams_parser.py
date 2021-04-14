import re

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstEventTeamsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Find what Teams are attending an Event, and return their team_numbers.
        """

        teamRe = re.compile(r'whats-going-on\/team\/(\d*)\?ProgramCode=FRC">(\d*)')

        teams = list()
        for first_tpid, team_number in teamRe.findall(html):
            team = dict()
            team["first_tpid"] = int(first_tpid)
            team["team_number"] = int(team_number)
            teams.append(team)

        soup = BeautifulSoup(html)
        more_pages = soup.find('a', {'title': 'Go to next page'}) is not None
        return teams, more_pages

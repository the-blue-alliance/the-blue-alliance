import re

from datafeeds.parser_base import ParserBase


class UsfirstLegacyEventTeamsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Find what Teams are attending an Event, and return their team_numbers.
        """
        # This code is based on TeamTpidHelper.
        # -gregmarra 5 Dec 2010

        teamRe = re.compile(r'tpid=[A-Za-z0-9=&;\-:]*?">\d+')
        teamNumberRe = re.compile(r'\d+$')
        tpidRe = re.compile(r'\d+')

        teams = []
        for teamResult in teamRe.findall(html):
            team = dict()
            team["team_number"] = int(teamNumberRe.findall(teamResult)[0])
            team["first_tpid"] = int(tpidRe.findall(teamResult)[0])
            teams.append(team)

        return teams, False

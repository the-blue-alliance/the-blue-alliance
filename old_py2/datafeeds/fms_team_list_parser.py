import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class FmsTeamListParser(ParserBase):
    """
    Facilitates getting information about Teams from USFIRST.
    Reads from FMS data pages, which are mostly tab delimited files wrapped in some HTML.
    Note, this doesn't get team websites.
    """

    @classmethod
    def parse(self, html):
        """
        Parse the information table on USFIRSTs site to extract team information.
        Return a list of dictionaries of team data.
        """
        teams = list()
        soup = BeautifulSoup(html)

        for title in soup.findAll('title'):
            if "FRC Team/Event List" not in title.string:
                return None

        team_rows = soup.findAll("pre")[0].string.split("\n")

        for line in team_rows[2:]:  # first is blank, second is headers.
            data = line.split("\t")
            if len(data) > 1:
                try:
                    teams.append({
                        "team_number": int(data[1]),
                        "name": data[2],
                        "short_name": data[3],
                        "nickname": data[7]
                    })
                except Exception, e:
                    logging.warning("Failed to parse team row: %s" % data)

        return teams, False

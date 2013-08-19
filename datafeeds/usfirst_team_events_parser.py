import re

from datafeeds.parser_base import ParserBase


class UsfirstTeamEventsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse team page on USFIRSTs site to extract FIRST event_ids for events
        that the team has attended. Return a list of event_id.
        """
        team_event_re = r'/whats-going-on/event/([0-9]+)'

        first_eids = re.findall(team_event_re, html)

        return first_eids, False

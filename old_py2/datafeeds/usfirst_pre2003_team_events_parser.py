import re

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstPre2003TeamEventsParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse team page on USFIRSTs site to extract FIRST event_ids for events
        that the team has attended. Return a list of event_id.
        """
        team_event_re = r'/whats-going-on/event/([0-9]+)'

        soup = BeautifulSoup(html)

        first_eids = []
        history_table = soup.find('div', {'class': 'team-history-wrapper'}).findAll('table')[0]
        for tr in history_table.findAll('tr')[1:]:  # skip table title row
            trs = tr.findAll('td')
            year = int(trs[0].text)
            if year < 2003:
                eid = re.findall(team_event_re, str(trs[1]))[0]
                first_eids.append(eid)

        return first_eids, False

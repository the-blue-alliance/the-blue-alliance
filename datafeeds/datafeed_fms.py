import logging

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.fms_event_list_parser import FmsEventListParser
from datafeeds.fms_team_list_parser import FmsTeamListParser

from models.event import Event
from models.team import Team


class DatafeedFms(DatafeedBase):

    FMS_EVENT_LIST_URL = "https://my.usfirst.org/frc/scoring/index.lasso?page=eventlist"
    # Raw fast teamlist, no tpids
    FMS_TEAM_LIST_URL = "https://my.usfirst.org/frc/scoring/index.lasso?page=teamlist"

    def __init__(self, *args, **kw):
        super(DatafeedFms, self).__init__(*args, **kw)

    def getFmsEventList(self):
        events, _ = self.parse(self.FMS_EVENT_LIST_URL, FmsEventListParser)

        return [
            Event(
                id="%s%s" % (event.get("year", None),
                             event.get("event_short", None)),
                end_date=event.get("end_date", None),
                event_short=event.get("event_short", None),
                first_eid=event.get("first_eid", None),
                name=event.get("name", None),
                official=True,
                start_date=event.get("start_date", None),
                venue=event.get("venue", None),
                year=event.get("year", None)) for event in events
        ]

    def getFmsTeamList(self):
        teams, _ = self.parse(self.FMS_TEAM_LIST_URL, FmsTeamListParser)

        return [
            Team(
                id="frc%s" % team.get("team_number", None),
                name=self._shorten(team.get("name", None)),
                nickname=self._shorten(team.get("nickname", None)),
                team_number=team.get("team_number", None)) for team in teams
        ]

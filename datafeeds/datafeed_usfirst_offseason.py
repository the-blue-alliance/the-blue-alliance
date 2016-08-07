import datetime
import logging

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import tba_config

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.usfirst_event_offseason_list_parser import UsfirstEventOffseasonListParser

from models.event import Event


class DatafeedUsfirstOffseason(DatafeedBase):
    EVENT_OFFSEASON_LIST_URL = "http://www.firstinspires.org/robotics/frc/calendar?field_event_category_tid=416"

    def getEventList(self):
        events, _ = self.parse(self.EVENT_OFFSEASON_LIST_URL, UsfirstEventOffseasonListParser)

        return [Event(
            event_type_enum=event.get("event_type_enum", None),
            event_short="???",
            first_eid=event.get("first_eid", None),
            name=event.get("name", None),
            year=datetime.datetime.now().year,
            start_date=event.get("start_date", None),
            end_date=event.get("end_date", None),
            state_prov=event.get("state_prov", None),
            )
            for event in events]

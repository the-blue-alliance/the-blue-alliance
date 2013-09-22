import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from datafeeds.datafeed_usfirst_offseason import DatafeedUsfirstOffseason

from consts.event_type import EventType
from models.event import Event


class AdminOffseasonScraperController(LoggedInHandler):
    """
    View and add un-added offseasons from FIRST's site
    """
    def get(self):
        self._require_admin()

        df = DatafeedUsfirstOffseason()
        new_events = df.getEventList()
        old_events = Event.query().filter(
            Event.event_type_enum == EventType.OFFSEASON).filter(
            Event.year == 2013)

        self.template_values.update({
            "events": new_events,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/offseasons.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        # Write some stuff to databases

        self.redirect("/admin/offseasons")




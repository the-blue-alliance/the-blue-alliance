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
            Event.year == 2013).filter(
            Event.first_eid != None).fetch(100)

        old_first_eids = [event.first_eid for event in old_events]
        truly_new_events = [event for event in new_events if event.first_eid not in old_first_eids]

        logging.info(old_events)

        self.template_values.update({
            "events": truly_new_events,
            "event_key": self.request.get("event_key"),
            "success": self.request.get("success"),

        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/offseasons.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        if self.request.get("submit") == "duplicate":
            old_event = Event.get_by_id(self.request.get("duplicate_event_key"))
            old_event.first_eid = self.request.get("event_first_eid")
            old_event.put()

        self.redirect("/admin/offseasons?success=duplicate&event_key=%s" % self.request.get("duplicate_event_key"))

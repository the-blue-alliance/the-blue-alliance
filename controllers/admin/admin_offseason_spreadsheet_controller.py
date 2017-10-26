import datetime
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from datafeeds.datafeed_offseason_spreadsheet import DatafeedOffseasonSpreadsheet

from consts.event_type import EventType
from helpers.event_manipulator import EventManipulator
from models.event import Event


class AdminOffseasonSpreadsheetController(LoggedInHandler):
    """
    View and add un-added offseasons from a Google Sheet:
    https://docs.google.com/spreadsheet/ccc?key=0ApfHZGrvPfuAdHVZcTczVnhQVnh1RlNEdVFmM2c3Y1E
    """

    SHEET_KEY = "0ApfHZGrvPfuAdHVZcTczVnhQVnh1RlNEdVFmM2c3Y1E"

    def get(self):
        self._require_admin()

        df = DatafeedOffseasonSpreadsheet()
        new_events = df.getEventList(self.SHEET_KEY)
        old_events = Event.query().filter(
            Event.event_type_enum == EventType.OFFSEASON).filter(
                Event.year == datetime.datetime.now().year).fetch(100)

        old_titles = [event.name for event in old_events]
        truly_new_events = [
            event for event in new_events if event.name not in old_titles
        ]

        self.template_values.update({
            "events":
            truly_new_events,
            "event_key":
            self.request.get("event_key"),
            "success":
            self.request.get("success"),
        })

        path = os.path.join(
            os.path.dirname(__file__),
            '../../templates/admin/offseasons_spreadsheet.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        if self.request.get("submit") == "duplicate":

            # how to do this?

            self.redirect(
                "/admin/offseasons/spreadsheet?success=duplicate&event_key=%s"
                % self.request.get("duplicate_event_key"))
            return

        if self.request.get("submit") == "create":

            start_date = None
            if self.request.get("event_start_date"):
                start_date = datetime.datetime.strptime(
                    self.request.get("event_start_date"), "%Y-%m-%d")

            end_date = None
            if self.request.get("event_end_date"):
                end_date = datetime.datetime.strptime(
                    self.request.get("event_end_date"), "%Y-%m-%d")

            event_key = str(self.request.get("event_year")) + str.lower(
                str(self.request.get("event_short")))

            event = Event(
                id=event_key,
                event_type_enum=int(self.request.get("event_type_enum")),
                event_short=self.request.get("event_short"),
                name=self.request.get("event_name"),
                year=int(self.request.get("event_year")),
                start_date=start_date,
                end_date=end_date,
                location=self.request.get("event_location"),
                venue=self.request.get("event_venue"),
            )
            event = EventManipulator.createOrUpdate(event)

            self.redirect(
                "/admin/offseasons/spreadsheet?success=create&event_key=%s" %
                event_key)
            return

        self.redirect("/admin/offseasons/spreadsheet")

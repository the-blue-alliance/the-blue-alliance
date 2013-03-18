import datetime

from helpers.event_manipulator import EventManipulator
from models.event import Event

class EventTestCreator(object):
    @classmethod
    def createFutureEvent(self):
        event = Event(
            id = "{}testfuture".format(datetime.datetime.now().year),
            end_date = datetime.datetime.today() + datetime.timedelta(days=5),
            event_short = "testfuture",
            event_type = "Regional",
            first_eid = "5561",
            name = "Future Test Event",
            start_date = datetime.datetime.today() + datetime.timedelta(days=1),
            year = datetime.datetime.now().year,
            venue_address = "123 Fake Street, California, USA",
            website = "http://www.google.com"
        )
        return EventManipulator.createOrUpdate(event)

    @classmethod
    def createPresentEvent(self):
        event = Event(
            id = "{}testpresent".format(datetime.datetime.now().year),
            end_date = datetime.datetime.today() + datetime.timedelta(days=1),
            event_short = "testpresent",
            event_type = "Regional",
            first_eid = "5561",
            name = "Present Test Event",
            start_date = datetime.datetime.today() - datetime.timedelta(days=2),
            year = datetime.datetime.now().year,
            venue_address = "123 Fake Street, California, USA",
            website = "http://www.google.com"
        )
        return EventManipulator.createOrUpdate(event)

    @classmethod
    def createPastEvent(self):
        event = Event(
            id = "{}testpast".format(datetime.datetime.now().year),
            end_date = datetime.datetime.today() - datetime.timedelta(days=1),
            event_short = "testpast",
            event_type = "Regional",
            first_eid = "5561",
            name = "Past Test Event",
            start_date = datetime.datetime.today() - datetime.timedelta(days=5),
            year = datetime.datetime.now().year,
            venue_address = "123 Fake Street, California, USA",
            website = "http://www.google.com"
        )
        return EventManipulator.createOrUpdate(event)

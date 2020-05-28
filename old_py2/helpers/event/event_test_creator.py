import datetime

from consts.event_type import EventType
from helpers.event_manipulator import EventManipulator
from helpers.event_team.event_team_test_creator import EventTeamTestCreator
from helpers.match.match_test_creator import MatchTestCreator
from models.event import Event


class EventTestCreator(object):
    @classmethod
    def createFutureEvent(self, only_event=False):
        event = Event(
            id="{}testfuture".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today() + datetime.timedelta(days=12),
            event_short="testfuture",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Future Test Event",
            start_date=datetime.datetime.today() + datetime.timedelta(days=8),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com"
        )
        event = EventManipulator.createOrUpdate(event)
        if not only_event:
            EventTeamTestCreator.createEventTeams(event)
        return event

    @classmethod
    def createPresentEvent(self, only_event=False):
        id_string = "{}testpresent".format(datetime.datetime.now().year)
        event = Event(
            id=id_string,
            end_date=datetime.datetime.today() + datetime.timedelta(days=1),
            event_short="testpresent",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Present Test Event",
            start_date=datetime.datetime.today() - datetime.timedelta(days=2),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com",
            webcast_json="""[{"type":"ustream","channel":"6540154"}]"""
        )
        event = EventManipulator.createOrUpdate(event)
        if not only_event:
            EventTeamTestCreator.createEventTeams(event)
            mtc = MatchTestCreator(event)
            mtc.createCompleteQuals()
            mtc.createIncompleteQuals()
        return event

    @classmethod
    def createPastEvent(self, only_event=False):
        event = Event(
            id="{}testpast".format(datetime.datetime.now().year),
            end_date=datetime.datetime.today() - datetime.timedelta(days=8),
            event_short="testpast",
            event_type_enum=EventType.REGIONAL,
            first_eid="5561",
            name="Past Test Event",
            start_date=datetime.datetime.today() - datetime.timedelta(days=12),
            year=datetime.datetime.now().year,
            venue_address="123 Fake Street, California, USA",
            website="http://www.google.com"
        )
        event = EventManipulator.createOrUpdate(event)
        if not only_event:
            EventTeamTestCreator.createEventTeams(event)
            mtc = MatchTestCreator(event)
            mtc.createCompleteQuals()
        return event

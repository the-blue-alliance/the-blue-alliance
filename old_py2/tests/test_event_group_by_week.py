import unittest2
import time
import datetime
import random
import logging

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from helpers.event_helper import EventHelper, CHAMPIONSHIP_EVENTS_LABEL,\
    WEEKLESS_EVENTS_LABEL, OFFSEASON_EVENTS_LABEL, PRESEASON_EVENTS_LABEL
from models.event import Event


class TestEventGroupByWeek(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

    def test_group_by_week(self):
        """
        All events that start in the same span of Wednesday-Tuesday
        should be considered as being in the same week.
        """
        events_by_week = {}  # we will use this as the "answer key"

        # Generate random regional events
        seed = int(time.time())
        state = random.Random()
        state.seed(seed)

        event_id_counter = 0
        week_start = datetime.datetime(2013, 2, 27)
        for i in range(1, 7):  # test for 6 weeks
            for _ in range(state.randint(1, 15)):  # random number of events per week
                week_label = 'Week {}'.format(i)

                start_date = week_start + datetime.timedelta(days=state.randint(0, 6))
                end_date = start_date + datetime.timedelta(days=state.randint(0, 3))

                event = Event(
                    id='2013tst{}'.format(event_id_counter),
                    event_short='tst{}'.format(event_id_counter),
                    start_date=start_date,
                    end_date=end_date,
                    year=2013,
                    official=True,
                    event_type_enum=state.choice([EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP])
                )

                if week_label in events_by_week:
                    events_by_week[week_label].append(event)
                else:
                    events_by_week[week_label] = [event]

                event_id_counter += 1
            week_start = week_start + datetime.timedelta(days=7)

        # Generate Championship events
        week_start += datetime.timedelta(days=7)
        events_by_week[CHAMPIONSHIP_EVENTS_LABEL] = [
            Event(
                id='2013arc'.format(event_id_counter),
                event_short='arc',
                start_date=week_start,
                end_date=week_start + datetime.timedelta(days=2),
                year=2013,
                official=True,
                event_type_enum=EventType.CMP_DIVISION
            ),
            Event(
                id='2013gal'.format(event_id_counter),
                event_short='gal',
                start_date=week_start,
                end_date=week_start + datetime.timedelta(days=2),
                year=2013,
                official=True,
                event_type_enum=EventType.CMP_DIVISION
            ),
            Event(
                id='2013cmp'.format(event_id_counter),
                event_short='cmp',
                start_date=week_start + datetime.timedelta(days=2),
                end_date=week_start + datetime.timedelta(days=2),
                year=2013,
                official=True,
                event_type_enum=EventType.CMP_FINALS
            )
        ]

        # Generate official events with no dates
        events_by_week[WEEKLESS_EVENTS_LABEL] = [
            Event(
                id='2013weekless1'.format(event_id_counter),
                event_short='weekless1',
                year=2013,
                official=True,
                event_type_enum=state.choice([EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP])
            ),
            Event(
                id='2013weekless2'.format(event_id_counter),
                event_short='weekless2',
                year=2013,
                official=True,
                event_type_enum=state.choice([EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP])
            ),
            Event(
                id='2013weekless3'.format(event_id_counter),
                event_short='weekless3',
                year=2013,
                official=True,
                event_type_enum=state.choice([EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP])
            ),
            Event(
                id='2013weekless4'.format(event_id_counter),
                event_short='weekless4',
                start_date=datetime.datetime(2013, 12, 31),
                end_date=datetime.datetime(2013, 12, 31),
                year=2013,
                official=True,
                event_type_enum=state.choice([EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP])
            )
        ]

        # Generate preseason events
        events_by_week[PRESEASON_EVENTS_LABEL] = [
            Event(
                id='2013preseason1'.format(event_id_counter),
                event_short='preseason1',
                year=2013,
                official=False,
                event_type_enum=EventType.PRESEASON
            ),
            Event(
                id='2013preseason2'.format(event_id_counter),
                event_short='preseason2',
                start_date=datetime.datetime(2013, 1, 18),
                end_date=datetime.datetime(2013, 1, 20),
                year=2013,
                official=False,
                event_type_enum=EventType.PRESEASON
            ),
            Event(
                id='2013preseason3'.format(event_id_counter),
                event_short='preseason3',
                start_date=datetime.datetime(2013, 7, 11),
                end_date=datetime.datetime(2013, 7, 12),
                year=2013,
                official=False,
                event_type_enum=EventType.PRESEASON
            )
        ]

        # Generate offseason events. Offseason events are any event that doesn't fall under one of the above categories.
        events_by_week[OFFSEASON_EVENTS_LABEL] = [
            Event(
                id='2013offseason1'.format(event_id_counter),
                event_short='offseason1',
                year=2013,
                official=False,
                event_type_enum=EventType.OFFSEASON
            ),
            Event(
                id='2013offseason2'.format(event_id_counter),
                event_short='offseason2',
                start_date=datetime.datetime(2013, 8, 18),
                end_date=datetime.datetime(2013, 8, 20),
                year=2013,
                official=False,
                event_type_enum=EventType.OFFSEASON
            ),
            Event(
                id='2013offseason3'.format(event_id_counter),
                event_short='offseason3',
                start_date=datetime.datetime(2013, 12, 30),
                end_date=datetime.datetime(2013, 12, 31),
                year=2013,
                official=False,
                event_type_enum=EventType.OFFSEASON
            ),
            Event(
                id='2013offseason4'.format(event_id_counter),
                event_short='offseason4',
                start_date=datetime.datetime(2013, 11, 13),
                end_date=datetime.datetime(2013, 11, 14),
                year=2013,
                official=False,
                event_type_enum=EventType.REGIONAL
            )
        ]

        # Combine all events and shufle randomly
        events = []
        for week_events in events_by_week.values():
            events.extend(week_events)
        state.shuffle(events)
        ndb.put_multi(events)

        # Begin testing
        events.sort(key=EventHelper.distantFutureIfNoStartDate)
        week_events = EventHelper.groupByWeek(events)

        for key in events_by_week.keys():
            try:
                self.assertEqual(set([e.key.id() for e in events_by_week[key]]),
                                 set([e.key.id() for e in week_events[key]]))
            except AssertionError, e:
                logging.warning("\n\nseed: {}".format(seed))
                logging.warning("\n\nkey: {}".format(key))
                logging.warning("\n\nevents_by_week: {}".format(events_by_week[key]))
                logging.warning("\n\nweek_events: {}".format(week_events[key]))
                raise e

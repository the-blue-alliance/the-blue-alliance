import json
import logging
import datetime
import re

from google.appengine.api import memcache
from google.appengine.ext import ndb

from consts.event_type import EventType

from models.district import District
from models.event import Event
from models.match import Match


class EventHelper(object):
    """
    Helper class for Events.
    """

    @classmethod
    def getTeamWLT(self, team_key, event):
        """
        Given a team_key, and an event, find the team's Win Loss Tie.
        """
        match_keys = Match.query(Match.event == event.key, Match.team_key_names == team_key).fetch(500, keys_only=True)
        return self.calculate_wlt(team_key, ndb.get_multi(match_keys))

    @classmethod
    def week_events(self):
        """
        Get events this week
        In general, if an event is currently going on, it shows up in this query
        An event shows up in this query iff:
        a) The event is within_a_day
        OR
        b) The event.start_date is on or within 4 days after the closest Wednesday/Monday (pre-2020/post-2020)
        """
        event_keys = memcache.get('EventHelper.week_events():event_keys')
        if event_keys is not None:
            return ndb.get_multi(event_keys)

        today = datetime.datetime.today()

        # Make sure all events to be returned are within range
        two_weeks_of_events_keys_future = Event.query().filter(
          Event.start_date >= (today - datetime.timedelta(weeks=1))).filter(
          Event.start_date <= (today + datetime.timedelta(weeks=1))).order(
          Event.start_date).fetch_async(keys_only=True)

        events = []

        diff_from_week_start = 0 - today.weekday()
        closest_start_monday = today + datetime.timedelta(days=diff_from_week_start)

        two_weeks_of_event_futures = ndb.get_multi_async(two_weeks_of_events_keys_future.get_result())
        for event_future in two_weeks_of_event_futures:
            event = event_future.get_result()
            if event.within_a_day:
                events.append(event)
            else:
                offset = event.start_date.date() - closest_start_monday.date()
                if (offset == datetime.timedelta(0)) or (offset > datetime.timedelta(0) and offset < datetime.timedelta(weeks=1)):
                    events.append(event)

        EventHelper.sort_events(events)
        memcache.set('EventHelper.week_events():event_keys', [e.key for e in events], 60*60)
        return events

    @classmethod
    def parseEventType(self, event_type_str):
        """
        Given an event_type_str from USFIRST, return the proper event type
        Examples:
        'Regional' -> EventType.REGIONAL
        'District' -> EventType.DISTRICT
        'District Championship' -> EventType.DISTRICT_CMP
        'MI FRC State Championship' -> EventType.DISTRICT_CMP
        'Championship Finals' -> EventType.CMP_FINALS
        'Championship' -> EventType.CMP_FINALS
        """
        event_type_str = event_type_str.lower()

        # Easy to parse
        if 'regional' in event_type_str:
            return EventType.REGIONAL
        elif 'offseason' in event_type_str:
            return EventType.OFFSEASON
        elif 'preseason' in event_type_str:
            return EventType.PRESEASON

        # Districts have multiple names
        if ('district' in event_type_str) or ('state' in event_type_str)\
           or ('region' in event_type_str) or ('qualif' in event_type_str):
            if 'championship' in event_type_str:
                if 'division' in event_type_str:
                    return EventType.DISTRICT_CMP_DIVISION
                return EventType.DISTRICT_CMP
            else:
                return EventType.DISTRICT

        # Everything else with 'champ' should be a Championship event
        if 'champ' in event_type_str:
            if 'division' in event_type_str:
                return EventType.CMP_DIVISION
            else:
                return EventType.CMP_FINALS

        # An event slipped through!
        logging.warn("Event type '{}' not recognized!".format(event_type_str))
        return EventType.UNLABLED

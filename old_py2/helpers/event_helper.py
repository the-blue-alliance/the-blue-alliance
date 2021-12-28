import json
import logging
import datetime
import re

from google.appengine.api import memcache
from google.appengine.ext import ndb

from consts.district_type import DistrictType
from consts.event_type import EventType

from models.district import District
from models.event import Event
from models.match import Match


class EventHelper(object):
    """
    Helper class for Events.
    """
    @classmethod
    def alliance_selections_to_points(self, event, multiplier, alliance_selections):
        team_points = {}
        try:
            if event.key.id() == "2015micmp":
                # Special case for 2015 Michigan District CMP, due to there being 16 alliances instead of 8
                # Uses max of 48 points and no multiplier
                # See 2015 Admin Manual, section 7.4.3.1
                # http://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/archive/2015/AdminManual20150407.pdf
                for n, alliance in enumerate(alliance_selections):
                    team_points[alliance['picks'][0]] = int(48 - (1.5 * n))
                    team_points[alliance['picks'][1]] = int(48 - (1.5 * n))
                    team_points[alliance['picks'][2]] = int((n + 1) * 1.5)
                    n += 1
            else:
                for n, alliance in enumerate(alliance_selections):
                    n += 1
                    team_points[alliance['picks'][0]] = (17 - n) * multiplier
                    team_points[alliance['picks'][1]] = (17 - n) * multiplier
                    team_points[alliance['picks'][2]] = n * multiplier
        except Exception, e:
            # Log only if this matters
            if event.district_key is not None:
                logging.error("Alliance points calc for {} errored!".format(event.key.id()))
                logging.exception(e)

        return team_points

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
    def getEventsWithinADay(self):
        event_keys = memcache.get('EventHelper.getEventsWithinADay():event_keys')
        if event_keys is not None:
            return ndb.get_multi(event_keys)

        events = filter(lambda e: e.within_a_day, self.week_events())
        memcache.set('EventHelper.getEventsWithinADay():event_keys', [e.key for e in events], 60*60)
        return events

    @classmethod
    def getShortName(self, name_str, district_code=None):
        """
        Extracts a short name like "Silicon Valley" from an event name like
        "Silicon Valley Regional sponsored by Google.org".

        See https://github.com/the-blue-alliance/the-blue-alliance-android/blob/master/android/src/test/java/com/thebluealliance/androidclient/test/helpers/EventHelperTest.java
        """
        district_keys = memcache.get('EventHelper.getShortName():district_keys')
        if not district_keys:
            codes = set([d.id()[4:].upper() for d in District.query().fetch(keys_only=True)])
            if district_code:
                codes.add(district_code.upper())
            if 'MAR' in codes:  # MAR renamed to FMA in 2019
                codes.add('FMA')
            if 'TX' in codes:  # TX and FIT used interchangeably
                codes.add('FIT')
            if 'IN' in codes:  # IN and FIN used interchangeably
                codes.add('FIN')
            district_keys = '|'.join(codes)
        memcache.set('EventHelper.getShortName():district_keys', district_keys, 60*60)

        # Account for 2020 suspensions
        if name_str.startswith("***SUSPENDED***"):
            name_str = name_str.replace("***SUSPENDED***", "")

        # 2015+ districts
        # Numbered events with no name
        re_string = '({}) District Event (#\d+)'.format(district_keys)
        match = re.match(re_string, name_str)
        if match:
            return '{} {}'.format(match.group(1).strip(), match.group(2).strip())
        # The rest
        re_string = '(?:{}) District -?(.+)'.format(district_keys)
        match = re.match(re_string, name_str)
        if match:
            partial = match.group(1).strip()
            match2 = re.sub(r'(?<=[\w\s])Event\s*(?:[\w\s]*$)?', '', partial)
            return match2.strip()

        # 2014- districts
        # district championships, other districts, and regionals
        name_str = re.sub(r'\s?Event','', name_str)
        match = re.match(r'\s*(?:MAR |PNW |)(?:FIRST Robotics|FRC|)(.+)(?:District|Regional|Region|Provincial|State|Tournament|FRC|Field)(?:\b)(?:[\w\s]+?(#\d*)*)?', name_str)

        if match:
            short = ''.join(match.groups(''))
            match = re.match(r'(.+)(?:FIRST Robotics|FRC)', short)
            if match:
                result = match.group(1).strip()
            else:
                result = short.strip()
            if result.startswith('FIRST'):
                result = result[5:]
            return result.strip()

        return name_str.strip()

    @classmethod
    def parseDistrictName(cls, district_name_str):
        district = DistrictType.names.get(district_name_str, DistrictType.NO_DISTRICT)

        # Fall back to checking abbreviations if needed
        return district if district != DistrictType.NO_DISTRICT else DistrictType.abbrevs.get(district_name_str, DistrictType.NO_DISTRICT)

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

import logging
import collections
import datetime

from google.appengine.ext import ndb

from consts.event_type import EventType

from models.event import Event
from models.match import Match
from models.team import Team

CHAMPIONSHIP_EVENTS = set(['arc', 'cur', 'gal', 'new', 'ein', 'cmp'])
CHAMPIONSHIP_EVENTS_LABEL = 'Championship Event'
REGIONAL_EVENTS_LABEL = 'Week {}'
WEEKLESS_EVENTS_LABEL = 'Other Official Events'
OFFSEASON_EVENTS_LABEL = 'Offseason'


class EventHelper(object):
    """
    Helper class for Events.
    """
    @classmethod
    def groupByWeek(self, events):
        """
        Events should already be ordered by start_date
        """
        toReturn = collections.OrderedDict()  # key: week_label, value: list of events

        current_week = 1
        week_start = None
        offseason_events = []
        weekless_events = []
        for event in events:
            start = event.start_date

            if event.event_short in CHAMPIONSHIP_EVENTS:
                if CHAMPIONSHIP_EVENTS_LABEL in toReturn:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL].append(event)
                else:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL] = [event]
                continue
            elif not event.official:
                offseason_events.append(event)
            elif start.month != 12 or start.day != 31:
                if week_start is None:
                    diff_from_thurs = start.weekday() - 3   # 3 is Thursday
                    week_start = start + datetime.timedelta(days=diff_from_thurs)

                if start >= week_start + datetime.timedelta(days=7):
                    current_week += 1
                    week_start += datetime.timedelta(days=7)

                label = REGIONAL_EVENTS_LABEL.format(current_week)
                if label in toReturn:
                    toReturn[label].append(event)
                else:
                    toReturn[label] = [event]
            else:
                weekless_events.append(event)

        # Add weekless + other events last
        if weekless_events:
            toReturn[WEEKLESS_EVENTS_LABEL] = weekless_events
        if offseason_events:
            toReturn[OFFSEASON_EVENTS_LABEL] = offseason_events

        return toReturn

    @classmethod
    def distantFutureIfNoStartDate(self, event):
        if not event.start_date:
            return datetime.datetime(2177, 1, 1, 1, 1, 1)
        else:
            return event.start_date

    @classmethod
    def calculateTeamWLTFromMatches(self, team_key, matches):
        """
        Given a team_key and some matches, find the Win Loss Tie.
        """
        wlt = {"win": 0, "loss": 0, "tie": 0}

        for match in matches:
            if match.has_been_played and match.winning_alliance is not None:
                if match.winning_alliance == "":
                    wlt["tie"] += 1
                elif team_key in match.alliances[match.winning_alliance]["teams"]:
                    wlt["win"] += 1
                else:
                    wlt["loss"] += 1
        return wlt

    @classmethod
    def getTeamWLT(self, team_key, event):
        """
        Given a team_key, and an event, find the team's Win Loss Tie.
        """
        match_keys = Match.query(Match.event == event.key, Match.team_key_names == team_key).fetch(500, keys_only=True)
        return self.calculateTeamWLTFromMatches(team_key, ndb.get_multi(match_keys))

    @classmethod
    def getWeekEvents(self):
        """
        Get events this week
        In general, if an event is currently going on, it shows up in this query
        An event shows up in this query iff:
        a) The event is within_a_day
        OR
        b) The event.start_date is on or within 4 days after the closest Thursday
        """
        today = datetime.datetime.today()

        # Make sure all events to be returned are within range
        two_weeks_of_events_keys_future = Event.query().filter(
          Event.start_date >= (today - datetime.timedelta(days=7))).filter(
          Event.start_date <= (today + datetime.timedelta(days=7))).order(
          Event.start_date).fetch_async(50, keys_only=True)

        events = []
        diff_from_thurs = 3 - today.weekday()  # 3 is Thursday. diff_from_thurs ranges from 3 to -3 (Monday thru Sunday)
        closest_thursday = today + datetime.timedelta(days=diff_from_thurs)

        two_weeks_of_events = ndb.get_multi(two_weeks_of_events_keys_future.get_result())
        for event in two_weeks_of_events:
            if event.within_a_day:
                events.append(event)
            else:
                offset = event.start_date.date() - closest_thursday.date()
                if (offset == datetime.timedelta(0)) or (offset > datetime.timedelta(0) and offset < datetime.timedelta(4)):
                    events.append(event)

        return events

    @classmethod
    def getEventsWithinADay(self):
        week_events = self.getWeekEvents()
        ret = []
        for event in week_events:
            if event.within_a_day:
                ret.append(event)
        return ret

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

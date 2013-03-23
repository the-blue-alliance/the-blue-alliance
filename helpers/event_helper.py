import logging
import collections
import datetime

from models.event import Event
from models.match import Match
from models.team import Team

CHAMPIONSHIP_EVENTS = set(['arc', 'cur', 'gal', 'new', 'ein', 'cmp'])
CHAMPIONSHIP_EVENTS_LABEL = 'Championship Event'
REGIONAL_EVENTS_LABEL = 'Week {}'
OFFSEASON_EVENTS_LABEL = 'Offseason'
WEEKLESS_EVENTS_LABEL = 'Other Official Events'


class EventHelper(object):
    """
    Helper class for Events.
    """
    @classmethod
    def groupByWeek(self, events):
        """
        Events should already be ordered by start_date
        Works for years 2005 and above
        """
        toReturn = collections.OrderedDict()  # key: week_label, value: list of events
        
        current_week = 1
        week_start = None
        offseason_events = []
        weekless_events = []
        for event in events:
            if not event.start_date:
                weekless_events.append(event)
                break

            start = event.start_date

            if event.event_short in CHAMPIONSHIP_EVENTS:
                if CHAMPIONSHIP_EVENTS_LABEL in toReturn:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL].append(event)
                else:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL] = [event]
                continue
            elif not event.official:
                offseason_events.append(event)
            else:
                if week_start == None:
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
            if match.has_been_played and match.winning_alliance != None:
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
        matches = Match.query(Match.event == event.key, Match.team_key_names == team_key).fetch(500)
        return self.calculateTeamWLTFromMatches(team_key, matches)
      
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
        
        two_weeks_of_events = Event.query() # Make sure all events to be returned are within range
        two_weeks_of_events = two_weeks_of_events.filter(Event.start_date >= (today - datetime.timedelta(days=7)))
        two_weeks_of_events = two_weeks_of_events.filter(Event.start_date <= (today + datetime.timedelta(days=7)))
        two_weeks_of_events = two_weeks_of_events.order(Event.start_date)
        two_weeks_of_events = two_weeks_of_events.fetch(50)
        
        events = []
        diff_from_thurs = 3 - today.weekday() # 3 is Thursday. diff_from_thurs ranges from 3 to -3 (Monday thru Sunday)
        closest_thursday = today + datetime.timedelta(days=diff_from_thurs)
        
        for event in two_weeks_of_events:
            if event.within_a_day:
                events.append(event)
            else:
                offset = event.start_date.date() - closest_thursday.date()
                if (offset == datetime.timedelta(0)) or (offset > datetime.timedelta(0) and offset < datetime.timedelta(4)):
                    events.append(event)
                    
        return events

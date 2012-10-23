import logging
import collections
import datetime

from models.event import Event
from models.match import Match
from models.team import Team

CHAMPIONSHIP_EVENTS = set(['arc', 'cur', 'gal', 'new', 'ein', 'cmp'])
CHAMPIONSHIP_EVENTS_LABEL = 'Championship Event'
REGIONAL_EVENTS_LABEL = 'Week {} Events'
OFFSEASON_EVENTS_LABEL = 'Offseason Events'


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
        for event in events:
            start = event.start_date

            if event.event_short in CHAMPIONSHIP_EVENTS:
                if CHAMPIONSHIP_EVENTS_LABEL in toReturn:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL].append(event)
                else:
                    toReturn[CHAMPIONSHIP_EVENTS_LABEL] = [event]
                continue
            elif (start == None) or (start.month > 4):
                label = OFFSEASON_EVENTS_LABEL
                if label in toReturn:
                    toReturn[label].append(event)
                else:
                    toReturn[label] = [event]
                continue
            else:
                if week_start == None:
                    diff_from_thurs = start.weekday() - 3   # 3 is Thursday
                    week_start = start + datetime.timedelta(days=diff_from_thurs)

                if start >= week_start + datetime.timedelta(days=6):
                    current_week += 1
                    week_start += datetime.timedelta(days=7)
                    
                label = REGIONAL_EVENTS_LABEL.format(current_week)
                if label in toReturn:
                    toReturn[label].append(event)
                else:
                    toReturn[label] = [event]
        
        return toReturn
    
    @classmethod
    def getTeamWLTFromMatches(self, team_key, matches):
        """
        Given a team_key and some matches, find the Win Loss Tie.
        """
        wlt = {"win": 0, "loss": 0, "tie": 0}
        
        for match in matches:
            if match.has_been_played and match.winning_alliance:
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
        return self.getTeamWLTFromMatches(team_key, matches)

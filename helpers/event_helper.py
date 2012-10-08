import logging

from google.appengine.ext import db

from models.event import Event
from models.match import Match
from models.team import Team

class EventHelper(object):
    """
    Helper class for Events.
    """
    
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

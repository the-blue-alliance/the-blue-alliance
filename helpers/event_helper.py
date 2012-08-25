import logging

from google.appengine.ext import db

from models.event import Event
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
            if match.has_been_played:
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
        matches = event.match_set.filter("team_key_names =", team_key)
        return self.getTeamWLTFromMatches(team_key, matches)

class EventUpdater(object):
    """
    Helper class to handle Event objects when we are not sure whether they
    already exist or not.
    """
    
    @classmethod
    def createOrUpdate(self, new_event):
        """
        Take an Event object, and either update the Event it is a newer
        version of, or create the Event if it is totally new.
        """
        event = self.findOrSpawn(new_event)
        event.put()
        return event
    
    @classmethod
    def findOrSpawn(self, new_event):
        """"
        Check if an event currently exists in the database based on key_name.
        Doesn't put objects.
        If it does, update it and give it back.
        If it does not, give it back.
        """
        query = Event.all()
        
        # First, look for a key_name collision.
        event = Event.get_by_key_name(new_event.key_name)
        if event is not None:
            event = self.updateMerge(new_event, event)
            return event
        
        # Don't see it, give it back.
        return new_event
    
    @classmethod
    def updateMerge(self, new_event, old_event):
        """
        Given an "old" and a "new" Event object, replace the fields in the
        "old" event that are present in the "new" event, but keep fields from
        the "old" event that are null or the empty list in the "new" event.
        We need to be careful, because ListProperty defaults to [] instead of
        None.
        """
        
        for attr, value in vars(new_event).iteritems():
            try:
                # If value is a non-empty list or string set it in old_event.
                if len(value)>0:
                    setattr(old_event,attr,value)
                
                # If the string is "None", write None
                if value == "None":
                    setattr(old_event,attr,None)
            except Exception:
                # An exception was raised because value is None. We don't do
                # anything so that old_event retains whatever value it had.
                pass


        return old_event

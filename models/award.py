from google.appengine.ext import ndb

from models.event import Event
from models.team import Team

class Award(ndb.Model):
    """
    Awards represent FIRST Robotics Competition awards given out at an event.
    name is a general name and can be seen in /datafeeds/datafeed_usfirst_awards.py
    key_name is like '2012sj_rca'
    """
    name = ndb.StringProperty(required=True) #general name used for sorting
    official_name = ndb.StringProperty(indexed=False) #the official name used by first
    year = ndb.IntegerProperty() #year it was awarded
    team = ndb.KeyProperty(kind=Team) #team that won the award (if applicable)
    awardee = ndb.StringProperty() #person who won the award (if applicable)
    event = ndb.KeyProperty(kind=Event, required=True)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)
    
    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Award object before writing it.
        """
        return self.renderKeyName(self.event.id(), self.name)

    @classmethod
    def renderKeyName(self, event_id, name):
        return str(event_id) + '_' + str(name)

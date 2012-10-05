from google.appengine.ext import db

from models.event import Event
from models.team import Team

class Award(db.Model):
    """
    Awards represent FIRST Robotics Competition awards given out at an event.
    name is a general name and can be seen in /datafeeds/datafeed_usfirst_awards.py
    key_name is like '2012sj_rca'
    """
    name = db.StringProperty(required=True) #general name used for sorting
    official_name = db.StringProperty(indexed=False) #the official name used by first
    year = db.IntegerProperty() #year it was awarded
    team = db.ReferenceProperty(Team) #team that won the award (if applicable)
    awardee = db.StringProperty() #person who won the award (if applicable)
    event = db.ReferenceProperty(Event, required=True)
    
    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Award object before writing it.
        """
        return self.getKeyName(self.event, self.name)

    @classmethod
    def getKeyName(self, event, name):
        return str(event.key_name) + '_' + str(name)

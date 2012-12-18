from google.appengine.ext import ndb

from models.event import Event
from models.team import Team

class Award(ndb.Model):
    """
    Awards represent FIRST Robotics Competition awards given out at an event.
    name is a general name and can be seen in /datafeeds/datafeed_usfirst_awards.py
    key_name is like '2012sj_rca'
    """

    # For checking if an award falls in one of the following categories
    REGIONAL_WIN_KEYS = set(['win1', 'win2', 'win3', 'win4'])
    REGIONAL_CA_KEYS = set(['ca', 'ca1', 'ca2'])
    DIVISION_WIN_KEYS = set(['div_win1', 'div_win2', 'div_win3', 'div_win4'])
    DIVISION_FIN_KEYS = set(['div_fin1', 'div_fin2', 'div_fin3', 'div_fin'])
    CHAMPIONSHIP_WIN_KEYS = set(['cmp_win1', 'cmp_win2', 'cmp_win3', 'cmp_win4'])
    CHAMPIONSHIP_FIN_KEYS = set(['cmp_fin1', 'cmp_fin2', 'cmp_fin3', 'cmp_fin4'])
    CHAMPIONSHIP_CA_KEYS = set(['cmp_ca'])
    BLUE_BANNER_KEYS = set(REGIONAL_WIN_KEYS.union(REGIONAL_CA_KEYS).union(DIVISION_WIN_KEYS).union(CHAMPIONSHIP_WIN_KEYS).union(CHAMPIONSHIP_CA_KEYS))
    
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

from google.appengine.ext import ndb

from models.event import Event
from models.team import Team


class EventTeam(ndb.Model):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    key_name is like 2010cmp_frc177 or 2007ct_frc195
    """
    event = ndb.KeyProperty(kind=Event)
    team = ndb.KeyProperty(kind=Team)
    year = ndb.IntegerProperty()

    status = ndb.JsonProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'event': set(),
            'team': set(),
            'year': set(),
        }
        super(EventTeam, self).__init__(*args, **kw)

    @property
    def key_name(self):
        return self.event.id() + "_" + self.team.id()

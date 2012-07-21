from google.appengine.ext import db

from models.event import Event
from models.team import Team

class EventTeam(db.Model):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    key_name is like 2010cmp_frc177 or 2007ct_frc195
    """
    event = db.ReferenceProperty(Event,
                                 collection_name='teams')
    team = db.ReferenceProperty(Team,
                                collection_name='events')
    year = db.IntegerProperty()
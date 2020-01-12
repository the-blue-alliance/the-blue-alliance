from google.appengine.ext import ndb
from models.event import Event


class ZebraMotionWorks(ndb.Model):
    """
    The ZebraMotionWorks model represents robot tracking data from the
    Zebra MotionWorks system
    """
    event = ndb.KeyProperty(kind=Event, required=True)
    data = ndb.JsonProperty(required=True)

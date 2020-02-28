import datetime
from google.appengine.ext import ndb
from models.event import Event


class ZebraMotionWorks(ndb.Model):
    """
    The ZebraMotionWorks model represents robot tracking data from the
    Zebra MotionWorks system
    """
    event = ndb.KeyProperty(kind=Event, required=True)
    data = ndb.JsonProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False, default=datetime.datetime.fromtimestamp(0))
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False, default=datetime.datetime.fromtimestamp(0))

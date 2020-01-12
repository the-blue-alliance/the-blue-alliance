from google.appengine.ext import ndb


class ZebraMotionWorks(ndb.Model):
    """
    The ZebraMotionWorks model represents robot tracking data from the
    Zebra MotionWorks system
    """
    data = ndb.JsonProperty(required=True)

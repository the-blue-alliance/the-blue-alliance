from google.appengine.ext import ndb


class ZebraMotion(ndb.Model):
    """
    The ZebraMotion model represents robot tracking data from the
    Zebra MotionWorks system
    """
    data = ndb.JsonProperty(required=True)

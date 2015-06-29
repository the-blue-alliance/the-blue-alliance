from google.appengine.ext import ndb


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """
    result = ndb.PickleProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

from google.appengine.ext import ndb


class TypeaheadEntry(ndb.Model):
    """
    """
    data_json = ndb.StringProperty(required=True, indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

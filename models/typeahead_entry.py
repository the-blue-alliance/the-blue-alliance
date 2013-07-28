from google.appengine.ext import ndb


class TypeaheadEntry(ndb.Model):
    """
    Model for storing precomputed typeahead entries as keys and values, where
    TypeaheadEntry.id (set in cron_controller.TypeaheadCalcDo) is the key and
    TypeaheadEntry.data_json is the value.
    """
    data_json = ndb.StringProperty(required=True, indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

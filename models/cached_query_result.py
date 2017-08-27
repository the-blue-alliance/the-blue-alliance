from google.appengine.ext import ndb


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """
    # Only one of result or result_dict should ever be populated for one model
    result_dict_full = ndb.JsonProperty(compressed=True)  # Entire serialized result
    result_dict = ndb.JsonProperty()  # Dict version of models (for API)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

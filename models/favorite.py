from google.appengine.ext import ndb


class Favorite(ndb.Model):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    model_type = ndb.IntegerProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(Favorite, self).__init__(*args, **kw)

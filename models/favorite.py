from google.appengine.ext import ndb

class Favorite(ndb.Model):

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)
    model_type = ndb.IntegerProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)

    def __init__(self, *args, **kw):
        super(Favorite, self).__init__(*args, **kw)


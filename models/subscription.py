from google.appengine.ext import ndb

class Subscription(ndb.Model):

    user_id = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)

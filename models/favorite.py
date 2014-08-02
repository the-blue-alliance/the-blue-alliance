from google.appengine.ext import ndb

class Favorite(ndb.Model):

    user_key = ndb.StringProperty(required=True)
    model_key = ndb.StringProperty(required=True)

    created = ndb.DateTimeProperty(auto_now_add=True)    

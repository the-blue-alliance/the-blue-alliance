from google.appengine.ext import db


class User(db.Model):
    # TBA ID
    id = db.StringProperty(required=True)
    # Created date and updated date
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    # User's full name
    name = db.StringProperty(required=True)
    # FB access token
    access_token = db.StringProperty(required=True)

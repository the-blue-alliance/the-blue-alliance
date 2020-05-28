from google.appengine.ext import ndb


class Account(ndb.Model):
    """
    Accounts represent accounts people use on TBA.
    """
    # Set by login/registration
    # Not editable by the user
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    registered = ndb.BooleanProperty()
    permissions = ndb.IntegerProperty(repeated=True)
    shadow_banned = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    # These optional properties are editable by the user
    display_name = ndb.StringProperty()

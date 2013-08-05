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

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    # These optional properties are editable by the user
    name = ndb.StringProperty()

    # Creates a greeting for the user based on whether or not they've set a name
    if name:
        greeting = name
    else:
        greeting = nickname

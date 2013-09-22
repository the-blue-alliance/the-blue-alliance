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

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    # These optional properties are editable by the user
    display_name = ndb.StringProperty()
    team_affiliation = ndb.IntegerProperty(default=0) #TODO: Check against current list of teams

    # User preferences
    # TODO: Add typeahead support for follow fields
    follow_teams = ndb.StringProperty()
    follow_events = ndb.StringProperty()
    gameday_layout = ndb.IntegerProperty(default=2)

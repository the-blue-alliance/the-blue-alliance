from webapp2_extras.appengine.auth.models import User
from google.appengine.ext.ndb import key, model

class Account(User):
    """
    Accounts represent accounts people use on TBA.
    """
    # Set by login/registration
    # Not editable by the user
    email = model.StringProperty()
    nickname = model.StringProperty()

    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True, indexed=False)


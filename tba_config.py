import os
from models.sitevar import Sitevar
from secrets import SESSION_KEY

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# For choosing what the main landing page displays
KICKOFF = 1
BUILDSEASON = 2
COMPETITIONSEASON = 3
OFFSEASON = 4
INSIGHTS = 5
CHAMPS = 6

# The CONFIG variables should have exactly the same structure between environments
# Eventually a test environment should be added. -gregmarra 17 Jul 2012
if DEBUG:
    CONFIG = {
        "env": "dev",
        "memcache": False,
        "response_cache": False,
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?auth={}"
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "response_cache": True,
        "firebase-url": "https://thebluealliance.firebaseio.com/{}.json?auth={}"
    }

CONFIG['landing_handler'] = INSIGHTS
CONFIG["static_resource_version"] = 7

# webapp2 session key
session_key_sitevar = Sitevar.get_by_id("session.key")
if session_key_sitevar is None:
  raise Exception("Missing sitevar: session.key. Can't allow authentication.")
SESSION_KEY = str(session_key_sitevar.contents['key'])

# Google Oauth credentials
google_secrets = Sitevar.get_by_id("google.secrets")
if google_secrets is None:
  raise Exception("Missing sitevar: google.secrets. Can't allow authentication.")
GOOGLE_APP_ID = str(google_secrets.contents['GOOGLE_APP_ID'])
GOOGLE_APP_SECRET = str(google_secrets.contents['GOOGLE_APP_SECRET'])

# In the future, add credentials for more providers here
AUTH_CONFIG = {
  'google'      : (GOOGLE_APP_ID, GOOGLE_APP_SECRET,
                  'profile email'),
}

# webapp2 config
app_config = {
  'webapp2_extras.sessions': {
    'cookie_name': '_mytba_login',
    'secret_key': SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_model': 'models.account.Account',
    'user_attributes': []
  }
}


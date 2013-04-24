import json
import os

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# For choosing what the main landing page displays
KICKOFF = 1
BUILDSEASON = 2
COMPETITIONSEASON = 3
OFFSEASON = 4

# The CONFIG variables should have exactly the same structure between environments
# Eventually a test environment should be added. -gregmarra 17 Jul 2012
if DEBUG:
    CONFIG = {
        "env": "dev",
        "memcache": False,
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?auth={}"
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "firebase-url": "https://thebluealliance.firebaseio.com/{}.json?auth={}"
    }

CONFIG['landing_handler'] = COMPETITIONSEASON
CONFIG["static_resource_version"] = 5
CONFIG['webapp2_extras.sessions'] = {'secret_key': '7674B2D97DEA0AC5DA452389BDD41E0DAB9B'}

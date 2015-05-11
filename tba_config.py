import os

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

MAX_YEAR = 2015

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

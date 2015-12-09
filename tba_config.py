import os

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev') or os.getenv('APPLICATION_ID') != 's~tbatv-prod-hrd'

MAX_YEAR = 2016

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
        "database_query_cache": False,
        "response_cache": False,
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?auth={}"
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "database_query_cache": True,
        "response_cache": True,
        "firebase-url": "https://thebluealliance.firebaseio.com/{}.json?auth={}"
    }

CONFIG['landing_handler'] = KICKOFF
CONFIG["static_resource_version"] = 7

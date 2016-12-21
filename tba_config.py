import os


DEBUG = os.environ.get('SERVER_SOFTWARE') is not None and os.getenv('APPLICATION_ID') != 's~tbatv-prod-hrd'
DEBUG = DEBUG or os.getenv('IS_TBA_TEST') is not None or os.getenv('TRAVIS') is not None

MAX_YEAR = 2017

# Fraction of requests to profile
RECORD_FRACTION = 0.1

# Fraction of requests to send to Google Analytics
GA_RECORD_FRACTION = 1.0

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
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?auth={}",
        "use-compiled-templates": False,
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "database_query_cache": True,
        "response_cache": True,
        "firebase-url": "https://thebluealliance.firebaseio.com/{}.json?auth={}",
        "use-compiled-templates": True
    }

CONFIG['landing_handler'] = KICKOFF
CONFIG["static_resource_version"] = 8

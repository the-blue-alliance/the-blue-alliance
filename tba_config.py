import datetime
import os
from consts.landing_type import LandingType
from models.sitevar import Sitevar


DEBUG = os.environ.get('SERVER_SOFTWARE') is not None and os.getenv('APPLICATION_ID') != 's~tbatv-prod-hrd'
DEBUG = DEBUG or os.getenv('IS_TBA_TEST') is not None or os.getenv('TRAVIS') is not None


# Fraction of requests to profile
RECORD_FRACTION = 0.1

# Fraction of requests to send to Google Analytics
GA_RECORD_FRACTION = 1.0

# The CONFIG variables should have exactly the same structure between environments
# Eventually a test environment should be added. -gregmarra 17 Jul 2012
if DEBUG:
    CONFIG = {
        "env": "dev",
        "memcache": False,
        "database_query_cache": False,
        "response_cache": False,
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?print=silent&auth={}",
        "firebase-push": False,
        "use-compiled-templates": False,
        "save-frc-api-response": False,
        "update-webcast-online-status": False,
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "database_query_cache": True,
        "response_cache": True,
        "firebase-url": "https://tbatv-prod-hrd.firebaseio.com/{}.json?print=silent&auth={}",
        "firebase-push": True,
        "use-compiled-templates": True,
        "save-frc-api-response": True,
        "update-webcast-online-status": True,
    }

CONFIG["static_resource_version"] = 8


def _get_max_year():
    DEFAULT_YEAR = datetime.datetime.now().year
    try:
        status_sitevar = Sitevar.get_by_id('apistatus')
        return status_sitevar.contents.get(
            'max_season', DEFAULT_YEAR) if status_sitevar else DEFAULT_YEAR
    except Exception:
        return DEFAULT_YEAR

MIN_YEAR = 1992
MAX_YEAR = _get_max_year()
VALID_YEARS = range(MIN_YEAR, MAX_YEAR + 1)

import json
import os

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# The CONFIG variables should have exactly the same structure between environments
# Eventually a test environment should be added. -gregmarra 17 Jul 2012
if DEBUG:
    CONFIG = {
        "env": "dev",
        "memcache": False,
        "firebase-url": "https://thebluealliance-dev.firebaseio.com/{}.json?print=silent&auth={}"
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
        "firebase-url": "https://thebluealliance.firebaseio.com/{}.json?print=silent&auth={}"
    }

CONFIG['kickoff'] = True
CONFIG["static_resource_version"] = 1

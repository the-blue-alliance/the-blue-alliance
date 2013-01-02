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
    }
else:
    CONFIG = {
        "env": "prod",
        "memcache": True,
    }

CONFIG['landing_handler'] = KICKOFF
CONFIG["static_resource_version"] = 2

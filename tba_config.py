import os

DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

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

CONFIG['kickoff'] = False

# Add your FB app info here
CONFIG['FACEBOOK_APP_ID'] = "YOUR_APP_ID"
CONFIG['FACEBOOK_APP_SECRET'] = "YOUR_SECRET"

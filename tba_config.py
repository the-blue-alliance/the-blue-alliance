import json
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

def load_secrets(secret_type):
    global CONFIG
    with open("secrets/%s.json" % secret_type, "r") as f:
        secrets = json.loads(f.read())
        for (secret_key, secret_value) in secrets.items():
            CONFIG[secret_key] = secret_value

load_secrets("facebook")
load_secrets("twitter")
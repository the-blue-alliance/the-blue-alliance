# Copy this file into secrets.py and set keys, secrets and scopes.

# This is a session secret key used by webapp2 framework.
# Get 'a random and long string' from here: 
# http://clsc.net/tools/random-string-generator.php
# or execute this from a python shell: import os; os.urandom(64)
SESSION_KEY = "AWVn380989Jr5n4xfSO3YlzwuoWp7Edx32r8z75IEhWHG595XT"

# Google APIs
GOOGLE_APP_ID = '911408716707-8b1v6m1jqkgnsdqm02alrf46k56eh3su.apps.googleusercontent.com'
GOOGLE_APP_SECRET = 'oWbYOdRG-r59hy75ZhdMFsB2'

# config that summarizes the above
AUTH_CONFIG = {
  # OAuth 2.0 providers
  'google'      : (GOOGLE_APP_ID, GOOGLE_APP_SECRET,
                  'profile email'),
}

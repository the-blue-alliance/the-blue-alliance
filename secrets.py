# Copy this file into secrets.py and set keys, secrets and scopes.

# This is a session secret key used by webapp2 framework.
# Get 'a random and long string' from here: 
# http://clsc.net/tools/random-string-generator.php
# or execute this from a python shell: import os; os.urandom(64)
SESSION_KEY = "l88AK4xIxcU4FokEn7M1Y3RlmAeHrfoEZicyPtzadCbuLtVYz65uyFYjwZkht7F"

# Google APIs
GOOGLE_APP_ID = '892192653518.apps.googleusercontent.com'
GOOGLE_APP_SECRET = 'csHnsLRlOicNxDbTCeUQnOoe'

# Facebook auth apis
FACEBOOK_APP_ID = '355556801220560'
FACEBOOK_APP_SECRET = '21a9fbf66a0e7ab2ae9da05a9ee8ae60'

# https://www.linkedin.com/secure/developer
LINKEDIN_CONSUMER_KEY = 'consumer key'
LINKEDIN_CONSUMER_SECRET = 'consumer secret'

# https://manage.dev.live.com/AddApplication.aspx
# https://manage.dev.live.com/Applications/Index
WL_CLIENT_ID = 'client id'
WL_CLIENT_SECRET = 'client secret'

# https://dev.twitter.com/apps
TWITTER_CONSUMER_KEY = 'oauth1.0a consumer key'
TWITTER_CONSUMER_SECRET = 'oauth1.0a consumer secret'

# https://foursquare.com/developers/apps
FOURSQUARE_CLIENT_ID = 'client id'
FOURSQUARE_CLIENT_SECRET = 'client secret'

# config that summarizes the above
AUTH_CONFIG = {
  # OAuth 2.0 providers
  'google'      : (GOOGLE_APP_ID, GOOGLE_APP_SECRET,
                  'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'),
  'facebook'    : (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
                  'user_about_me,email'),
  'windows_live': (WL_CLIENT_ID, WL_CLIENT_SECRET,
                  'wl.signin'),
  'foursquare'  : (FOURSQUARE_CLIENT_ID,FOURSQUARE_CLIENT_SECRET,
                  'authorization_code'),

  # OAuth 1.0 providers don't have scopes
  'twitter'     : (TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET),
  'linkedin'    : (LINKEDIN_CONSUMER_KEY, LINKEDIN_CONSUMER_SECRET),

  # OpenID doesn't need any key/secret
}

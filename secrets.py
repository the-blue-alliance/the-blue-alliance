from models.sitevar import Sitevar

facebook_secrets = Sitevar.get_by_id('facebook.secrets')

# Google APIs
#GOOGLE_APP_ID = '892192653518.apps.googleusercontent.com'
#GOOGLE_APP_SECRET = 'csHnsLRlOicNxDbTCeUQnOoe'

# Facebook auth apis
FACEBOOK_APP_ID = facebook_secrets.contents['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = facebook_secrets.contents['FACEBOOK_APP_SECRET']

# https://www.linkedin.com/secure/developer
#LINKEDIN_CONSUMER_KEY = 'consumer key'
#LINKEDIN_CONSUMER_SECRET = 'consumer secret'

# https://manage.dev.live.com/AddApplication.aspx
# https://manage.dev.live.com/Applications/Index
#WL_CLIENT_ID = 'client id'
#WL_CLIENT_SECRET = 'client secret'

# https://dev.twitter.com/apps
#TWITTER_CONSUMER_KEY = 'oauth1.0a consumer key'
#TWITTER_CONSUMER_SECRET = 'oauth1.0a consumer secret'

# https://foursquare.com/developers/apps
#FOURSQUARE_CLIENT_ID = 'client id'
#FOURSQUARE_CLIENT_SECRET = 'client secret'

# config that summarizes the above
AUTH_CONFIG = {
  # OAuth 2.0 providers
#  'google'      : (GOOGLE_APP_ID, GOOGLE_APP_SECRET,
 #                 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'),
  'facebook'    : (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
                  'user_about_me,email'),
#  'windows_live': (WL_CLIENT_ID, WL_CLIENT_SECRET,
#                  'wl.signin'),
#  'foursquare'  : (FOURSQUARE_CLIENT_ID,FOURSQUARE_CLIENT_SECRET,
#                  'authorization_code'),

  # OAuth 1.0 providers don't have scopes
#  'twitter'     : (TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET),
#  'linkedin'    : (LINKEDIN_CONSUMER_KEY, LINKEDIN_CONSUMER_SECRET),

  # OpenID doesn't need any key/secret
}

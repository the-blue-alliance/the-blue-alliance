# -*- coding: utf-8 -*-
import os
import sys
import logging

from urllib import urlencode
import urlparse

# for CSRF state tokens
import time
import base64

# Get available json parser
try:
  # should be the fastest on App Engine py27.
  import json
except ImportError:
  try: 
    import simplejson as json
  except ImportError:
    from django.utils import simplejson as json
    # at this point ImportError will be raised 
    # if none of the above could be imported

# it's a OAuth 1.0 spec even though the lib is called oauth2
import oauth2 as oauth1

# users module is needed for OpenID authentication.
from google.appengine.api import urlfetch, users
from webapp2_extras import security

__all__ = ['SimpleAuthHandler',
           'Error',
           'UnknownAuthMethodError',
           'AuthProviderResponseError',
           'InvalidCSRFTokenError',
           'InvalidOAuthRequestToken',
           'InvalidOpenIDUserError']


class Error(Exception):
  """Base error class for this module"""
  pass

class UnknownAuthMethodError(Error):
  """Raised when there's no method to call for a specific auth type"""
  pass

class AuthProviderResponseError(Error):
  """Error coming from a provider"""
  pass

class InvalidCSRFTokenError(Error):
  """Currently used only in OAuth 2.0 with CSRF protection enabled"""
  pass

class InvalidOAuthRequestToken(Error):
  """OAuth1 request token -related error"""
  pass

class InvalidOpenIDUserError(Error):
  """Error during OpenID auth callback"""
  pass


class SimpleAuthHandler(object):
  """A mixin to be used with a real request handler, 
  e.g. webapp2.RequestHandler. See README for getting started and 
  a usage example, or look through the code. It really is simple.

  See README for docs on authentication flows.
  """
  
  PROVIDERS = {
    'google'      : ('oauth2', 
      'https://accounts.google.com/o/oauth2/auth?{0}', 
      'https://accounts.google.com/o/oauth2/token'),
    'windows_live': ('oauth2',
      'https://login.live.com/oauth20_authorize.srf?{0}',
      'https://login.live.com/oauth20_token.srf'),
    'facebook'    : ('oauth2',
      'https://www.facebook.com/dialog/oauth?{0}',
      'https://graph.facebook.com/oauth/access_token'),
    'linkedin'    : ('oauth1', {
      'request': 'https://api.linkedin.com/uas/oauth/requestToken', 
      'auth'   : 'https://www.linkedin.com/uas/oauth/authenticate?{0}'
    },           'https://api.linkedin.com/uas/oauth/accessToken'),
    'twitter'     : ('oauth1', {
       'request': 'https://api.twitter.com/oauth/request_token', 
       'auth'   : 'https://api.twitter.com/oauth/authenticate?{0}'
    },            'https://api.twitter.com/oauth/access_token'),
    'foursquare': ('oauth2',
       'https://foursquare.com/oauth2/authenticate?{0}',
       'https://foursquare.com/oauth2/access_token'),
    'openid'      : ('openid', None)
  }
  
  
  TOKEN_RESPONSE_PARSERS = {
    'google'      : '_json_parser',
    'windows_live': '_json_parser',
    'foursquare'  : '_json_parser',
    'facebook'    : '_query_string_parser',
    'linkedin'    : '_query_string_parser',
    'twitter'     : '_query_string_parser'
  }

  # Set this to True in your handler if you want to use 
  # 'state' param during authorization phase to guard agains
  # cross-site-request-forgery
  # 
  # CSRF protection assumes there's self.session method on the handler 
  # instance. See BaseRequestHandler in example/handlers.py for sample usage.
  OAUTH2_CSRF_STATE = False
  OAUTH2_CSRF_SESSION_PARAM = 'oauth2_state'
  OAUTH2_CSRF_TOKEN_TIMEOUT = 3600 # 1 hour
  # This will form the actual state parameter, e.g. token:timestamp
  # You don't normally need to override it.
  OAUTH2_CSRF_DELIMITER = ':'
  
  def _simple_auth(self, provider=None):
    """Dispatcher of auth init requests, e.g.
    GET /auth/PROVIDER
    
    Calls _<authtype>_init() method, where <authtype> is
    oauth2, oauth1 or openid (defined in PROVIDERS dict).
    
    May raise one of the exceptions defined at the beginning
    of the module. See README for details on error handling.
    """
    cfg = self.PROVIDERS.get(provider, (None,))
    meth = self._auth_method(cfg[0], 'init')
    # We don't respond directly in here. Specific methods are in charge
    # with redirecting user to an auth endpoint
    meth(provider, cfg[1])
      
  def _auth_callback(self, provider=None):
    """Dispatcher of callbacks from auth providers, e.g.
    /auth/PROVIDER/callback?params=...
    
    Calls _<authtype>_callback() method, where <authtype> is
    oauth2, oauth1 or openid (defined in PROVIDERS dict).
    
    May raise one of the exceptions defined at the beginning
    of the module. See README for details on error handling.
    """
    cfg = self.PROVIDERS.get(provider, (None,))
    meth = self._auth_method(cfg[0], 'callback')
    # Get user profile data and their access token
    user_data, auth_info = meth(provider, *cfg[-1:])
    # The rest should be implemented by the actual app
    self._on_signin(user_data, auth_info, provider)

  def _auth_method(self, auth_type, step):
    """Constructs proper method name and returns a callable.

    Args:
      auth_type: string, One of 'oauth2', 'oauth1' or 'openid'
      step: string, Phase of the auth flow. Either 'init' or 'callback'

    Raises UnknownAuthMethodError if expected method doesn't exist on the
    handler instance processing the request.
    """
    method = '_%s_%s' % (auth_type, step)
    try:
      return getattr(self, method)
    except AttributeError:
      raise UnknownAuthMethodError(method)

  def _oauth2_init(self, provider, auth_url):
    """Initiates OAuth 2.0 web flow"""
    key, secret, scope = self._get_consumer_info_for(provider)
    callback_url = self._callback_uri_for(provider)

    params = {
      'response_type': 'code',
      'client_id': key, 
      'redirect_uri': callback_url 
    }

    if scope:
      params.update(scope=scope)

    if self.OAUTH2_CSRF_STATE:
      state = self._generate_csrf_token()
      params.update(state=state)
      self.session[self.OAUTH2_CSRF_SESSION_PARAM] = state

    target_url = auth_url.format(urlencode(params)) 
    logging.debug('Redirecting user to %s', target_url)

    self.redirect(target_url)      
    
  def _oauth2_callback(self, provider, access_token_url):
    """Step 2 of OAuth 2.0, whenever the user accepts or denies access."""
    error = self.request.get('error')
    if error:
      raise AuthProviderResponseError(error, provider)

    code = self.request.get('code')
    callback_url = self._callback_uri_for(provider)
    client_id, client_secret, scope = self._get_consumer_info_for(provider)

    if self.OAUTH2_CSRF_STATE:
      _expected = self.session.pop(self.OAUTH2_CSRF_SESSION_PARAM, '')
      _actual = self.request.get('state')
      # If _expected is '' it won't validate anyway.
      if not self._validate_csrf_token(_expected, _actual):
        raise InvalidCSRFTokenError(
          '[%s] vs [%s]' % (_expected, _actual), provider)
      
    payload = {
      'code': code,
      'client_id': client_id,
      'client_secret': client_secret,
      'redirect_uri': callback_url,
      'grant_type': 'authorization_code'
    }
    
    resp = urlfetch.fetch(
      url=access_token_url, 
      payload=urlencode(payload), 
      method=urlfetch.POST,
      headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    _parser = getattr(self, self.TOKEN_RESPONSE_PARSERS[provider])
    _fetcher = getattr(self, '_get_%s_user_info' % provider)

    auth_info = _parser(resp.content)
    user_data = _fetcher(auth_info, key=client_id, secret=client_secret)
    return (user_data, auth_info)
    
  def _oauth1_init(self, provider, auth_urls):
    """Initiates OAuth 1.0 dance"""
    key, secret = self._get_consumer_info_for(provider)
    callback_url = self._callback_uri_for(provider)
    token_request_url = auth_urls.get('request', None)
    auth_url = auth_urls.get('auth', None)
    _parser = getattr(self, self.TOKEN_RESPONSE_PARSERS[provider], None)
      
    # make a request_token request
    client = self._oauth1_client(consumer_key=key, consumer_secret=secret)
    resp, content = client.request(auth_urls['request'], "GET")
    
    if resp.status != 200:
      raise AuthProviderResponseError(
        '%s (status: %d)' % (content, resp.status), provider)
    
    # parse token request response
    request_token = _parser(content)
    if not request_token.get('oauth_token', None):
      raise AuthProviderResponseError(
        "Couldn't get a request token from %s" % str(request_token), provider)
      
    target_url = auth_urls['auth'].format(urlencode({
      'oauth_token': request_token.get('oauth_token', None),
      'oauth_callback': callback_url
    }))
    
    logging.debug('Redirecting user to %s', target_url)
    
    # save request token for later, the callback
    self.session['req_token'] = request_token
    self.redirect(target_url)      
    
  def _oauth1_callback(self, provider, access_token_url):
    """Third step of OAuth 1.0 dance."""
    request_token = self.session.pop('req_token', None)
    if not request_token:
      raise InvalidOAuthRequestToken(
        "No request token in user session", provider)

    verifier = self.request.get('oauth_verifier')
    if not verifier:
      raise AuthProviderResponseError(
        "No OAuth verifier was provided", provider)

    consumer_key, consumer_secret = self._get_consumer_info_for(provider)
    token = oauth1.Token(request_token['oauth_token'], 
                         request_token['oauth_token_secret'])
    token.set_verifier(verifier)
    client = self._oauth1_client(token, consumer_key, consumer_secret)
    resp, content = client.request(access_token_url, "POST")

    _parser = getattr(self, self.TOKEN_RESPONSE_PARSERS[provider])
    _fetcher = getattr(self, '_get_%s_user_info' % provider)

    auth_info = _parser(content)
    user_data = _fetcher(auth_info, key=consumer_key, secret=consumer_secret)
    return (user_data, auth_info)
    
  def _openid_init(self, provider='openid', identity=None):
    """Initiates OpenID dance using App Engine users module API."""
    identity_url = identity or self.request.get('identity_url')
    callback_url = self._callback_uri_for(provider)

    target_url = users.create_login_url(
      dest_url=callback_url, federated_identity=identity_url)
    logging.debug('Redirecting user to %s', target_url)
    self.redirect(target_url)
      
  def _openid_callback(self, provider='openid', _identity=None):
    """Being called back by an OpenID provider 
    after the user has been authenticated.
    """
    user = users.get_current_user()
    
    if not user or not user.federated_identity():
      raise InvalidOpenIDUserError(user, provider)
      
    uinfo = {
      'id'      : user.federated_identity(),
      'nickname': user.nickname(),
      'email'   : user.email()
    }
    
    return (uinfo, {'provider': user.federated_provider()})

    
  #
  # callbacks and consumer key/secrets
  #
  
  def _callback_uri_for(self, provider):
    """Returns a callback URL for a 2nd step of the auth process.
    
    Override this with something like:
    self.uri_for('auth_callback', provider=provider, _full=True)
    """
    return None
    
  def _get_consumer_info_for(self, provider):
    """Returns a (key, secret, desired_scopes) tuple.

    Defaults to None. You should redefine this method and return real values.

    For OAuth 2.0 it should be a 3 elements tuple:
    (client_ID, client_secret, scopes)

    OAuth 1.0 doesn't have scope so this should return just a
    (consumer_key, consumer_secret) tuple.

    OpenID needs neither scope nor key/secret, so this method is never called
    for OpenID authentication.

    See README for more info on scopes and where to get consumer/client
    key/secrets.
    """
    return (None, None, None)
    
  #
  # user profile/info
  #
    
  def _get_google_user_info(self, auth_info, key=None, secret=None):
    """Returns a dict of currenly logging in user.
    Google API endpoint:
    https://www.googleapis.com/oauth2/v1/userinfo
    """
    resp = self._oauth2_request(
      'https://www.googleapis.com/oauth2/v1/userinfo?{0}', 
      auth_info['access_token']
    )
    return json.loads(resp)
    
  def _get_windows_live_user_info(self, auth_info, key=None, secret=None):
    """Windows Live API user profile endpoint.
    https://apis.live.net/v5.0/me
    
    Profile picture:
    https://apis.live.net/v5.0/USER_ID/picture
    """
    resp = self._oauth2_request('https://apis.live.net/v5.0/me?{0}', 
                                auth_info['access_token'])
    uinfo = json.loads(resp)
    avurl = 'https://apis.live.net/v5.0/{0}/picture'.format(uinfo['id'])
    uinfo.update(avatar_url=avurl)
    return uinfo
    
  def _get_facebook_user_info(self, auth_info, key=None, secret=None):
    """Facebook Graph API endpoint.
    https://graph.facebook.com/me
    """
    resp = self._oauth2_request('https://graph.facebook.com/me?{0}', 
                                auth_info['access_token'])
    return json.loads(resp)
    
  def _get_foursquare_user_info(self, auth_info, key=None, secret=None):
    """Returns a dict of currenly logging in user.
    foursquare API endpoint:
    https://api.foursquare.com/v2/users/self
    """
    resp = self._oauth2_request(
      'https://api.foursquare.com/v2/users/self?{0}&v=20130204',
      auth_info['access_token'],'oauth_token'
    )
    data = json.loads(resp)
    if data['meta']['code'] != 200:
      logging.error(data['meta']['errorDetail'])
    return data['response'].get('user')

  def _get_linkedin_user_info(self, auth_info, key=None, secret=None):
    """Returns a dict of currently logging in linkedin user.

    LinkedIn user profile API endpoint:
    http://api.linkedin.com/v1/people/~
    or
    http://api.linkedin.com/v1/people/~:<fields>
    where <fields> is something like
    (id,first-name,last-name,picture-url,public-profile-url,headline)
    """
    try:
        # already in the App Engine libs, see app.yaml on how to specify
        # libraries need this for providers like LinkedIn
        from lxml import etree
    except ImportError:
        logging.error('requirement `lxml.etree` was not provided. please '
                      'make sure you have enabled it in app.yaml')
        raise

    token = oauth1.Token(key=auth_info['oauth_token'], 
                         secret=auth_info['oauth_token_secret'])
    client = self._oauth1_client(token, key, secret)

    fields = 'id,first-name,last-name,picture-url,public-profile-url,headline'
    url = 'http://api.linkedin.com/v1/people/~:(%s)' % fields
    resp, content = client.request(url)
    
    person = etree.fromstring(content)
    uinfo = {}
    for e in person:
      uinfo.setdefault(e.tag, e.text)
    
    return uinfo
    
  def _get_twitter_user_info(self, auth_info, key=None, secret=None):
    """Returns a dict of twitter user using
    https://api.twitter.com/1/account/verify_credentials.json
    """
    token = oauth1.Token(key=auth_info['oauth_token'],
                         secret=auth_info['oauth_token_secret'])
    client = self._oauth1_client(token, key, secret)
    
    resp, content = client.request(
      'https://api.twitter.com/1/account/verify_credentials.json'
    )
    uinfo = json.loads(content)
    uinfo.setdefault('link', 'http://twitter.com/%s' % uinfo['screen_name'])
    return uinfo
    
  #
  # aux methods
  #
  
  def _oauth1_client(self, token=None, consumer_key=None, 
                     consumer_secret=None):
    """Returns OAuth 1.0 client that is capable of signing requests."""
    args = [oauth1.Consumer(key=consumer_key, secret=consumer_secret)]
    if token:
      args.append(token)
    
    return oauth1.Client(*args)
  
  def _oauth2_request(self, url, token, token_param='access_token'):
    """Makes an HTTP request with OAuth 2.0 access token using App Engine 
    URLfetch API.
    """
    target_url = url.format(urlencode({token_param:token}))
    return urlfetch.fetch(target_url).content
    
  def _query_string_parser(self, body):
    """Parses response body of an access token request query and returns
    the result in JSON format.
    
    Facebook, LinkedIn and Twitter respond with a query string, not JSON.
    """
    return dict(urlparse.parse_qsl(body))
    
  def _json_parser(self, body):
    """Parses body string into JSON dict"""
    return json.loads(body)

  def _generate_csrf_token(self, _time=None):
    """Creates a new random token that can be safely used as a URL param.

    Token would normally be stored in a user session and passed as 'state' 
    parameter during OAuth 2.0 authorization step.
    """
    now = str(_time or long(time.time()))
    secret = security.generate_random_string(30, pool=security.ASCII_PRINTABLE)
    token = self.OAUTH2_CSRF_DELIMITER.join([secret, now])
    return base64.urlsafe_b64encode(token)

  def _validate_csrf_token(self, expected, actual):
    """Validates expected token against the actual.

    Args:
      expected: String, existing token. Normally stored in a user session.
      actual: String, token provided via 'state' param.
    """
    if expected != actual:
      return False

    try:
      decoded = base64.urlsafe_b64decode(expected.encode('ascii'))
      token_key, token_time = decoded.rsplit(self.OAUTH2_CSRF_DELIMITER, 1)
      token_time = long(token_time)
      if not token_key:
        return False
    except (TypeError, ValueError, UnicodeDecodeError):
      return False

    now = long(time.time())
    timeout = now - token_time > self.OAUTH2_CSRF_TOKEN_TIMEOUT

    if timeout:
      logging.error("CSRF token timeout (issued at %d)", token_time)

    return not timeout

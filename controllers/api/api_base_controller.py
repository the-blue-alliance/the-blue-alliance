import datetime
import json
import logging
import md5
import random
import tba_config
import urllib
import uuid
import webapp2

from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from consts.auth_type import AuthType
from controllers.base_controller import CacheableHandler
from datafeeds.parser_base import ParserInputException
from helpers.user_bundle import UserBundle
from helpers.validation_helper import ValidationHelper
from models.api_auth_access import ApiAuthAccess
from models.cached_response import CachedResponse
from models.event import Event
from models.sitevar import Sitevar


# used for deferred call
def track_call(api_action, api_label, x_tba_app_id):
    """
    For more information about GAnalytics Protocol Parameters, visit
    https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    """
    analytics_id = Sitevar.get_by_id("google_analytics.id")
    if analytics_id is None:
        logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        GOOGLE_ANALYTICS_ID = analytics_id.contents['GOOGLE_ANALYTICS_ID']
        payload = urllib.urlencode({
            'v': 1,
            'tid': GOOGLE_ANALYTICS_ID,
            'cid': uuid.uuid3(uuid.NAMESPACE_X500, str(x_tba_app_id)),
            't': 'event',
            'ec': 'api-v02',
            'ea': api_action,
            'el': api_label,
            'cd1': x_tba_app_id,  # custom dimension 1
            'ni': 1,
            'sc': 'end',  # forces tracking session to end
        })

        urlfetch.fetch(
            url='https://www.google-analytics.com/collect',
            validate_certificate=True,
            method=urlfetch.POST,
            deadline=30,
            payload=payload,
        )


class ApiBaseController(CacheableHandler):

    API_VERSION = 2

    def __init__(self, *args, **kw):
        super(ApiBaseController, self).__init__(*args, **kw)
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.headers['Access-Control-Allow-Origin'] = '*'

    def handle_exception(self, exception, debug):
        """
        Handle an HTTP exception and actually writeout a
        response.
        Called by webapp when abort() is called, stops code excution.
        """
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            self.response.out.write(self._errors)
        else:
            logging.exception(exception)
            self.response.set_status(500)

    def get(self, *args, **kw):
        self._validate_tba_app_id()
        self._errors = ValidationHelper.validate(self._validators)
        if self._errors:
            self.abort(400)

        self._track_call(*args, **kw)
        super(ApiBaseController, self).get(*args, **kw)
        self.response.headers['X-TBA-Version'] = '{}'.format(self.API_VERSION)
        self.response.headers['Vary'] = 'Accept-Encoding'

    def options(self, *args, **kw):
        """
        Supply an OPTIONS method in order to comply with CORS preflghted requests
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
        """
        self.response.headers['Access-Control-Allow-Methods'] = "GET, OPTIONS"
        self.response.headers['Access-Control-Allow-Headers'] = 'X-TBA-App-Id'

    def _read_cache(self):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        response = CachedResponse.get_by_id(self.cache_key)
        if response:
            self._last_modified = response.updated
            return response
        else:
            return None

    def _write_cache(self, response):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        if tba_config.CONFIG["response_cache"]:
            CachedResponse(
                id=self.cache_key,
                headers_json=json.dumps(dict(response.headers)),
                body=response.body,
            ).put()

    @classmethod
    def delete_cache_multi(cls, cache_keys):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        logging.info("Deleting cache keys: {}".format(cache_keys))
        ndb.delete_multi([ndb.Key(CachedResponse, cache_key) for cache_key in cache_keys])

    def _track_call_defer(self, api_action, api_label):
        if random.random() < tba_config.GA_RECORD_FRACTION:
            deferred.defer(track_call, api_action, api_label, self.x_tba_app_id, _queue="api-track-call")

    def _validate_tba_app_id(self):
        """
        Tests the presence of a X-TBA-App-Id header or URL param.
        """
        self.x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
        if self.x_tba_app_id is None:
            self.x_tba_app_id = self.request.get('X-TBA-App-Id')

        logging.info("X-TBA-App-Id: {}".format(self.x_tba_app_id))
        if not self.x_tba_app_id:
            self._errors = json.dumps({"Error": "X-TBA-App-Id is a required header or URL param. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)

        x_tba_app_id_parts = self.x_tba_app_id.split(':')

        if len(x_tba_app_id_parts) != 3 or any(len(part) == 0 for part in x_tba_app_id_parts):
            self._errors = json.dumps({"Error": "X-TBA-App-Id must follow a specific format. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)


class ApiTrustedBaseController(webapp2.RequestHandler):
    REQUIRED_AUTH_TYPES = set()

    def __init__(self, *args, **kw):
        super(ApiTrustedBaseController, self).__init__(*args, **kw)
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self._user_bundle = UserBundle()

    def handle_exception(self, exception, debug):
        """
        Handle an HTTP exception and actually writeout a
        response.
        Called by webapp when abort() is called, stops code excution.
        """
        logging.info(exception)
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            self.response.out.write(self._errors)
        else:
            self.response.set_status(500)

    def options(self, event_key):
        """
        Supply an OPTIONS method in order to comply with CORS preflghted requests
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
        """
        self.response.headers['Access-Control-Allow-Methods'] = "POST, OPTIONS"
        self.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-TBA-Auth-Id, X-TBA-Auth-Sig'

    def _validate_auth(self, auth, event_key):
        allowed_event_keys = [ekey.id() for ekey in auth.event_list]
        if event_key not in allowed_event_keys:
            return "Only allowed to edit events: {}".format(', '.join(allowed_event_keys))

        missing_auths = self.REQUIRED_AUTH_TYPES.difference(set(auth.auth_types_enum))
        if missing_auths != set():
            return "You do not have permission to edit: {}. If this is incorrect, please contact TBA admin.".format(",".join([AuthType.type_names[ma] for ma in missing_auths]))

        if auth.expiration and auth.expiration < datetime.datetime.now():
            return "These keys expired on {}. Contact TBA admin to make changes".format(auth.expiration)

        return None

    def post(self, event_key):
        event_key = event_key.lower()  # Normalize keys to lower case (TBA convention)

        # Start by allowing admins to edit any event
        user_has_auth = (self._user_bundle.user and self._user_bundle.is_current_user_admin)

        if not user_has_auth and self._user_bundle.user:
            # See if this user has any auth keys granted to its account
            now = datetime.datetime.now()
            auth_tokens = ApiAuthAccess.query(ApiAuthAccess.owner == self._user_bundle.account.key,
                                              ApiAuthAccess.event_list == ndb.Key(Event, event_key),
                                              ndb.OR(ApiAuthAccess.expiration == None, ApiAuthAccess.expiration >= now)).fetch()
            user_has_auth = any(self._validate_auth(auth, event_key) is None for auth in auth_tokens)

        if not user_has_auth:
            # If not, check if auth id/secret were passed as headers
            auth_id = self.request.headers.get('X-TBA-Auth-Id')
            if not auth_id:
                self._errors = json.dumps({"Error": "Must provide a request header parameter 'X-TBA-Auth-Id'"})
                self.abort(400)

            auth_sig = self.request.headers.get('X-TBA-Auth-Sig')
            if not auth_sig:
                self._errors = json.dumps({"Error": "Must provide a request header parameter 'X-TBA-Auth-Sig'"})
                self.abort(400)

            auth = ApiAuthAccess.get_by_id(auth_id)
            expected_sig = md5.new('{}{}{}'.format(auth.secret if auth else None, self.request.path, self.request.body)).hexdigest()
            if not auth or expected_sig != auth_sig:
                logging.info("Auth sig: {}, Expected sig: {}".format(auth_sig, expected_sig))
                self._errors = json.dumps({"Error": "Invalid X-TBA-Auth-Id and/or X-TBA-Auth-Sig!"})
                self.abort(401)

            # Checks event key is valid, correct auth types, and expiration
            error = self._validate_auth(auth, event_key)
            if error:
                self._errors = json.dumps({"Error": error})
                self.abort(401)

        try:
            self._process_request(self.request, event_key)
        except ParserInputException, e:
            self._errors = json.dumps({"Error": e.message})
            self.abort(400)

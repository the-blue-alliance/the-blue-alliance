import datetime
import json
import logging
import md5
import random
import tba_config
import webapp2

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from consts.event_type import EventType
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
    from sitevars.google_analytics_id import GoogleAnalyticsID
    google_analytics_id = GoogleAnalyticsID.google_analytics_id()
    if not google_analytics_id:
        logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        import uuid
        cid = uuid.uuid3(uuid.NAMESPACE_X500, str(x_tba_app_id))

        from urllib import urlencode
        payload = urlencode({
            'v': 1,
            'tid': google_analytics_id,
            'cid': cid,
            't': 'event',
            'ec': 'api-v02',
            'ea': api_action,
            'el': api_label,
            'cd1': x_tba_app_id,  # custom dimension 1
            'ni': 1,
            'sc': 'end',  # forces tracking session to end
        })

        from google.appengine.api import urlfetch
        urlfetch.fetch(
            url='https://www.google-analytics.com/collect',
            validate_certificate=True,
            method=urlfetch.POST,
            deadline=30,
            payload=payload,
        )


class ApiBaseController(CacheableHandler):
    API_VERSION = 2
    SHOULD_ADD_ADMIN_BAR = False

    def __init__(self, *args, **kw):
        super(ApiBaseController, self).__init__(*args, **kw)
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['X-Robots-Tag'] = 'noindex'

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

        super(ApiBaseController, self).get(*args, **kw)
        self.response.headers['X-TBA-Version'] = '{}'.format(self.API_VERSION)
        self.response.headers['Vary'] = 'Accept-Encoding'

        if not self._errors:
            self._track_call(*args, **kw)

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
            deferred.defer(track_call, api_action, api_label, self.x_tba_app_id, _queue="api-track-call", _url='/_ah/queue/deferred_apiv2_track_call')

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
        status_sitevar_future = Sitevar.get_by_id_async('trustedapi')
        allowed_event_keys = [ekey.id() for ekey in auth.event_list]
        if event_key not in allowed_event_keys:
            return "Only allowed to edit events: {}".format(', '.join(allowed_event_keys))

        missing_auths = self.REQUIRED_AUTH_TYPES.difference(set(auth.auth_types_enum))
        if missing_auths != set():
            return "You do not have permission to edit: {}. If this is incorrect, please contact TBA admin.".format(",".join([AuthType.write_type_names[ma] for ma in missing_auths]))

        if auth.expiration and auth.expiration < datetime.datetime.now():
            return "These keys expired on {}. Contact TBA admin to make changes".format(auth.expiration)

        status_sitevar = status_sitevar_future.get_result()
        if status_sitevar:
            for auth_type in self.REQUIRED_AUTH_TYPES:
                if not status_sitevar.contents.get(str(auth_type), True):  # Fail open
                    return "The trusted API has been temporarily disabled by the TBA admins. Please contact them for more details."

        return None

    def post(self, event_key):
        event_key = event_key.lower()  # Normalize keys to lower case (TBA convention)

        # Make sure we are processing for a valid event first
        # (it's fine to do this before auth, since leaking the existence of an
        # event isn't really that big a deal)
        self.event = Event.get_by_id(event_key)
        if not self.event:
            self._errors = json.dumps({"Error": "Event {} not found".format(event_key)})
            self.abort(404)

        # Start by allowing admins to edit any event
        user_is_admin = (self._user_bundle.user and self._user_bundle.is_current_user_admin)

        # Also grant access if the user as the EVENTWIZARD permission and this
        # is a current year offseason event
        account = self._user_bundle.account
        current_year = datetime.datetime.now().year
        user_has_permission = (self.event.event_type_enum == EventType.OFFSEASON
            and self.event.year == current_year
            and account is not None
            and AccountPermissions.OFFSEASON_EVENTWIZARD in account.permissions)

        user_has_auth = (user_is_admin or user_has_permission)
        if not user_has_auth and self._user_bundle.user:
            # See if this user has any auth keys granted to its account
            now = datetime.datetime.now()
            auth_tokens = ApiAuthAccess.query(ApiAuthAccess.owner == account.key,
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

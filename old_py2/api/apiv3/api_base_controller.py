import json
import logging
import random
import tba_config
import time
import webapp2

from google.appengine.ext import deferred

from controllers.base_controller import CacheableHandler
from helpers.validation_helper import ValidationHelper
from models.api_auth_access import ApiAuthAccess
from stackdriver.profiler import TraceContext


# used for deferred call
def track_call(api_action, api_label, auth_owner, request_time):
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
        cid = uuid.uuid3(uuid.NAMESPACE_X500, str(auth_owner))

        from urllib import urlencode
        payloads = [
            urlencode({
                'v': 1,
                'tid': google_analytics_id,
                'cid': cid,
                't': 'event',
                'ec': 'api-v03',
                'ea': api_action,
                'el': api_label,
                'cd1': auth_owner,  # custom dimension 1
                'ni': 1,
                'sc': 'end',  # forces tracking session to end
            }),
            # urlencode({
            #     'v': 1,
            #     'tid': google_analytics_id,
            #     'cid': cid,
            #     't': 'timing',
            #     'utc': 'api-v03',
            #     'utv': api_action,
            #     'utt': request_time,
            # }),
        ]

        payload = '\n'.join(payloads)

        from google.appengine.api import urlfetch
        urlfetch.fetch(
            url='https://www.google-analytics.com/batch',
            validate_certificate=True,
            method=urlfetch.POST,
            deadline=30,
            payload=payload,
        )


class ApiBaseController(CacheableHandler):
    API_VERSION = 3
    REQUIRE_ADMIN_AUTH = False
    SHOULD_ADD_ADMIN_BAR = False

    def __init__(self, *args, **kw):
        self._request_start = time.time()
        super(ApiBaseController, self).__init__(*args, **kw)
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['X-Robots-Tag'] = 'noindex'

        # Set cache key based on class name, version, and kwargs
        kwargs_sorted = sorted([(k, v) for k, v in self.request.route_kwargs.items()], key=lambda x: x[0])
        self._partial_cache_key = '_'.join([
            'v{}_{}'.format(self.API_VERSION, self.__class__.__name__)] +
            [x[1] for x in kwargs_sorted])
        self._cache_expiration = self.CACHE_HEADER_LENGTH

    def handle_exception(self, exception, debug):
        """
        Handle an HTTP exception and actually writeout a
        response.
        Called by webapp when abort() is called, stops code excution.
        """
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            self.response.out.write(json.dumps(self._errors))
        else:
            logging.exception(exception)
            self.response.set_status(500)

    def get(self, *args, **kw):
        with TraceContext() as root:
            with root.span("ApiBaseController.get"):
                self._validate_tba_auth_key()
                self._errors = ValidationHelper.validate_request(self)
                if self._errors:
                    self.abort(404)

                super(ApiBaseController, self).get(*args, **kw)
                self.response.headers['X-TBA-Version'] = '{}'.format(self.API_VERSION)
                self.response.headers['Vary'] = 'Accept-Encoding'

        if not self._errors:
            self._track_call(*args, **kw)

    def post(self, *args, **kw):
        with TraceContext() as root:
            with root.span("ApiBaseController.post"):
                self._validate_tba_auth_key()
                self._errors = ValidationHelper.validate_request(self)
                if self._errors:
                    self.abort(404)

                rendered = self._render(*args, **kw)
                self.response.out.write(rendered)
                self.response.headers['X-TBA-Version'] = '{}'.format(self.API_VERSION)
                self.response.headers['Vary'] = 'Accept-Encoding'

                if not self._errors:
                    self._track_call(*args, **kw)

    def options(self, *args, **kw):
        """
        Supply an OPTIONS method in order to comply with CORS preflghted requests
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
        """
        self.response.headers['Access-Control-Allow-Methods'] = "GET, POST, OPTIONS"
        self.response.headers['Access-Control-Allow-Headers'] = 'X-TBA-Auth-Key, If-Modified-Since'
        self.response.headers['Access-Control-Max-Age'] = '604800'  # 1 week

    def _track_call_defer(self, api_action, api_label):
        if random.random() < tba_config.GA_RECORD_FRACTION:
            request_time = int(round(1000 * (time.time() - self._request_start)))
            deferred.defer(
                track_call,
                api_action, api_label,
                '{}:{}'.format(self.auth_owner, self.auth_description),
                request_time,
                _queue="api-track-call",
                _url='/_ah/queue/deferred_apiv3_track_call',
                _target='api',
            )

    def _validate_tba_auth_key(self):
        """
        Tests the presence of a X-TBA-Auth-Key header or URL param.
        """
        with TraceContext() as root:
            with root.span("ApiBaseController._validate_tba_auth_key"):
                x_tba_auth_key = self.request.headers.get("X-TBA-Auth-Key")
                if x_tba_auth_key is None:
                    x_tba_auth_key = self.request.get('X-TBA-Auth-Key')

                self.auth_owner = None
                self.auth_owner_key = None
                self.auth_description = None
                if not x_tba_auth_key:
                    account = self._user_bundle.account
                    if account:
                        self.auth_owner = account.key.id()
                        self.auth_owner_key = account.key
                    elif 'thebluealliance.com' in self.request.headers.get("Origin", ""):
                        self.auth_owner = 'The Blue Alliance'
                    else:
                        self._errors = {"Error": "X-TBA-Auth-Key is a required header or URL param. Please get an access key at http://www.thebluealliance.com/account."}
                        self.abort(401)

                if self.auth_owner:
                    logging.info("Auth owner: {}, LOGGED IN".format(self.auth_owner))
                else:
                    auth = ApiAuthAccess.get_by_id(x_tba_auth_key)
                    if auth and auth.is_read_key:
                        self.auth_owner = auth.owner.id()
                        self.auth_owner_key = auth.owner
                        self.auth_description = auth.description
                        if self.REQUIRE_ADMIN_AUTH and not auth.allow_admin:
                            self._errors = {"Error": "X-TBA-Auth-Key does not have required permissions"}
                            self.abort(401)
                        logging.info("Auth owner: {}, X-TBA-Auth-Key: {}".format(self.auth_owner, x_tba_auth_key))
                    else:
                        self._errors = {"Error": "X-TBA-Auth-Key is invalid. Please get an access key at http://www.thebluealliance.com/account."}
                        self.abort(401)


def handle_404(request, response, exception):
    response.headers['content-type'] = 'application/json; charset="utf-8"'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.write(json.dumps({"Error": "Invalid endpoint"}))
    response.set_status(404)

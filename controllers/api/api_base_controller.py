import json
import logging
import tba_config
import urllib
import uuid
import webapp2

from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler
from helpers.validation_helper import ValidationHelper
from models.cached_response import CachedResponse
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
        params = urllib.urlencode({
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

        analytics_url = 'http://www.google-analytics.com/collect?%s' % params
        urlfetch.fetch(
            url=analytics_url,
            method=urlfetch.GET,
            deadline=10,
        )


class ApiBaseController(CacheableHandler):

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
        logging.info(exception)
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
            self.response.out.write(self._errors)
        else:
            self.response.set_status(500)

    def get(self, *args, **kw):
        self._validate_tba_app_id()
        self._errors = ValidationHelper.validate(self._validators)
        if self._errors:
            self.abort(400)

        self._track_call(*args, **kw)
        super(ApiBaseController, self).get(*args, **kw)

    def _read_cache(self):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        response = CachedResponse.get_by_id(self.full_cache_key)
        if response:
            if self._has_been_modified_since(response.updated):
                response.headers['Last-Modified'] = self.response.headers['Last-Modified']
                return response
            else:
                return None

    def _write_cache(self, response):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        if tba_config.CONFIG["response_cache"]:
            CachedResponse(
                id=self.full_cache_key,
                headers_json=json.dumps(dict(response.headers)),
                body=response.body,
            ).put()

    @classmethod
    def _delete_cache(cls, full_cache_key):
        """
        Overrides parent method to use CachedResponse instead of memcache
        """
        ndb.Key(CachedResponse, full_cache_key).delete()

    def _track_call_defer(self, api_action, api_label):
        deferred.defer(track_call, api_action, api_label, self.x_tba_app_id)

    def _validate_tba_app_id(self):
        """
        Tests the presence of a X-TBA-App-Id header or URL param.
        """
        self.x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
        if self.x_tba_app_id is None:
            self.x_tba_app_id = self.request.get('X-TBA-App-Id')

        logging.info("X-TBA-App-ID: {}".format(self.x_tba_app_id))
        if not self.x_tba_app_id:
            self._errors = json.dumps({"Error": "X-TBA-App-Id is a required header or URL param. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)

        x_tba_app_id_parts = self.x_tba_app_id.split(':')

        if len(x_tba_app_id_parts) != 3 or any(len(part) == 0 for part in x_tba_app_id_parts):
            self._errors = json.dumps({"Error": "X-TBA-App-Id must follow a specific format. Please see http://www.thebluealliance.com/apidocs for more info."})
            self.abort(400)

    def _set_cache_header_length(self, seconds):
        if type(seconds) is not int:
            logging.error("Cache-Control max-age is not integer: {}".format(seconds))
            return

        self.response.headers['Cache-Control'] = "public, max-age=%d" % seconds
        self.response.headers['Pragma'] = 'Public'

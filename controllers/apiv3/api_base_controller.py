# import datetime
# import json
import logging
# import md5
# import random
# import tba_config
# import urllib
# import uuid
import webapp2

# from google.appengine.api import urlfetch
# from google.appengine.ext import deferred
# from google.appengine.ext import ndb

# from consts.auth_type import AuthType
from controllers.base_controller import CacheableHandler
# from datafeeds.parser_base import ParserInputException
# from helpers.user_bundle import UserBundle
from helpers.validation_helper import ValidationHelper
# from models.api_auth_access import ApiAuthAccess
# from models.cached_response import CachedResponse
# from models.event import Event
# from models.sitevar import Sitevar


# # used for deferred call
# def track_call(api_action, api_label, x_tba_app_id):
#     """
#     For more information about GAnalytics Protocol Parameters, visit
#     https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
#     """
#     analytics_id = Sitevar.get_by_id("google_analytics.id")
#     if analytics_id is None:
#         logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
#     else:
#         GOOGLE_ANALYTICS_ID = analytics_id.contents['GOOGLE_ANALYTICS_ID']
#         payload = urllib.urlencode({
#             'v': 1,
#             'tid': GOOGLE_ANALYTICS_ID,
#             'cid': uuid.uuid3(uuid.NAMESPACE_X500, str(x_tba_app_id)),
#             't': 'event',
#             'ec': 'api-v03',
#             'ea': api_action,
#             'el': api_label,
#             'cd1': x_tba_app_id,  # custom dimension 1
#             'ni': 1,
#             'sc': 'end',  # forces tracking session to end
#         })

#         urlfetch.fetch(
#             url='https://www.google-analytics.com/collect',
#             validate_certificate=True,
#             method=urlfetch.POST,
#             deadline=30,
#             payload=payload,
#         )


class ApiBaseController(CacheableHandler):
    API_VERSION = 3

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
        # self._validate_tba_app_id()
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
        # self.response.headers['Access-Control-Allow-Headers'] = 'X-TBA-App-Id'

    def _track_call_defer(self, api_action, api_label):
        return
        # if random.random() < tba_config.GA_RECORD_FRACTION:
        #     deferred.defer(track_call, api_action, api_label, self.x_tba_app_id, _queue="api-track-call")

    # def _validate_tba_app_id(self):
    #     """
    #     Tests the presence of a X-TBA-App-Id header or URL param.
    #     """
    #     self.x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
    #     if self.x_tba_app_id is None:
    #         self.x_tba_app_id = self.request.get('X-TBA-App-Id')

    #     logging.info("X-TBA-App-Id: {}".format(self.x_tba_app_id))
    #     if not self.x_tba_app_id:
    #         self._errors = json.dumps({"Error": "X-TBA-App-Id is a required header or URL param. Please see http://www.thebluealliance.com/apidocs for more info."})
    #         self.abort(400)

    #     x_tba_app_id_parts = self.x_tba_app_id.split(':')

    #     if len(x_tba_app_id_parts) != 3 or any(len(part) == 0 for part in x_tba_app_id_parts):
    #         self._errors = json.dumps({"Error": "X-TBA-App-Id must follow a specific format. Please see http://www.thebluealliance.com/apidocs for more info."})
    #         self.abort(400)

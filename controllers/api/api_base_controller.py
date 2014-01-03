import json
import logging
import webapp2

from controllers.base_controller import CacheableHandler
from helpers.validation_helper import ValidationHelper


class ApiBaseController(CacheableHandler):

    def __init__(self, *args, **kw):
        super(ApiBaseController, self).__init__(*args, **kw)
        self.response.headers['content-type'] = 'application/json; charset="utf-8"'

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

        super(ApiBaseController, self).get(*args, **kw)

    def _validate_tba_app_id(self):
        """
        Tests the presence of a X-TBA-App-Id header.
        """
        x_tba_app_id = self.request.headers.get("X-TBA-App-Id")
        if not x_tba_app_id:
            self._errors = json.dumps({"Error": "X-TBA-App-Id is a required header."})
            self.abort(400)
        if len(x_tba_app_id.split(':')) != 3:
            self._errors = json.dumps({"Error": "X-TBA-App-Id must follow the following format: <team/person id>:<app description>:<version>"})
            self.abort(400)
        logging.info("X-TBA-App-ID: {}".format(x_tba_app_id))

    def _write_cache_headers(self, seconds):
        if type(seconds) is not int:
            logging.error("Cache-Control max-age is not integer: {}".format(seconds))
            return

        self.response.headers['Cache-Control'] = "public, max-age=%d" % seconds
        self.response.headers['Pragma'] = 'Public'

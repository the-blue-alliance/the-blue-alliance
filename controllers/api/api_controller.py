import json
import logging
import webapp2

from controllers.base_controller import CacheableHandler
from helpers.validation_helper import ValidationHelper

class ApiController(CacheableHandler):

    def __init__(self, *args, **kw):
        super(ApiController, self).__init__(*args, **kw)
        self.response.content_type = 'application/json'

    def handle_exception(self, exception, debug):
        if isinstance(exception, webapp2.HTTPException):
            self.response.write(self.errors)

    def get(self, *args, **kw):
        self.errors = ValidationHelper.validate(self._validators)
        if self.errors:
            self.response.set_status(400)

        super(ApiController, self).get(*args, **kw)

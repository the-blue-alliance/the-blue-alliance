import json
from base_controller import LoggedInHandler
from helpers.apiai_helper import APIAIHelper


class APIAIHandler(LoggedInHandler):
    def __init__(self, *args, **kw):
        super(APIAIHandler, self).__init__(*args, **kw)

    def post(self):
        # TODO: Authentication

        request = json.loads(self.request.body)

        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.out.write(json.dumps(APIAIHelper.process_request(request)))

import json
from base_controller import LoggedInHandler
from helpers.apiai_helper import APIAIHelper
from models.sitevar import Sitevar


class APIAIHandler(LoggedInHandler):
    def __init__(self, *args, **kw):
        super(APIAIHandler, self).__init__(*args, **kw)

    def post(self):
        if self.request.headers.get('X-TBA-APIAI-Auth') != Sitevar.get_by_id('apiai.secrets').contents['key']:
            return

        request = json.loads(self.request.body)

        self.response.headers['content-type'] = 'application/json; charset="utf-8"'
        self.response.out.write(json.dumps(APIAIHelper.process_request(request)))

import logging
import json

from google.appengine.api import taskqueue


class FirebaseHelper(object):
    @classmethod
    def pushMatch(self, match):
        payload = {'key_name': match.key_name,
                   'alliances': match.alliances,
                   'winning_alliance': match.winning_alliance}
        payload_json = json.dumps(payload)

        taskqueue.add(url='/tasks/do/firebase_push', 
                      method='GET',
                      params={'key': 'last_matches',
                              'payload_json': payload_json})

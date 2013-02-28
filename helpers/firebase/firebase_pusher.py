import logging
import json

from google.appengine.api import taskqueue


class FirebasePusher(object):
    @classmethod
    def pushMatch(self, match):
        payload = {'key_name': match.key_name,
                   'comp_level': match.comp_level,
                   'match_number': match.match_number,
                   'set_number': match.set_number,
                   'alliances': match.alliances,
                   'winning_alliance': match.winning_alliance}
        payload_json = json.dumps(payload)

        taskqueue.add(url='/tasks/posts/firebase_push', 
                      method='GET',
                      queue_name='firebase',
                      params={'key': 'last_matches',
                              'payload_json': payload_json})

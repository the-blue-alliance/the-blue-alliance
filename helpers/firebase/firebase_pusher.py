import logging
import json

from google.appengine.api import taskqueue


class FirebasePusher(object):
    @classmethod
    def match_to_payload_dict(self, match):
        return {'key_name': match.key_name,
                'comp_level': match.comp_level,
                'match_number': match.match_number,
                'set_number': match.set_number,
                'alliances': match.alliances,
                'winning_alliance': match.winning_alliance}
         
    @classmethod
    def updateEvent(self, event, last_matches, upcoming_matches):
        last_matches_payload = []
        for match in last_matches:
            last_matches_payload.append(self.match_to_payload_dict(match))

        upcoming_matches_payload = []
        for match in upcoming_matches:
            upcoming_matches_payload.append(self.match_to_payload_dict(match))
            
        payload = {'last_matches': last_matches_payload,
                   'upcoming_matches': upcoming_matches_payload}
        payload_json = json.dumps(payload)
        
        taskqueue.add(url='/tasks/posts/firebase_push', 
                      method='GET',
                      queue_name='firebase',
                      params={'key': event.key_name,
                              'payload_json': payload_json})

import logging

from google.appengine.api import taskqueue


class FirebaseHelper(object):
    @classmethod
    def pushMatch(self, match_key, match_data):
        taskqueue.add(url='/tasks/do/firebase_push', 
                      method='GET',
                      params={'key': 'matches/{}'.format(match_key),
                              'payload': match_data})

import unittest2
import webapp2
import webtest
from google.appengine.ext import testbed
from google.appengine.ext import ndb
from webapp2_extras.routes import RedirectRoute

from consts.event_type import EventType
from controllers.suggestions.suggest_event_media_controller import SuggestEventMediaController
from models.account import Account
from models.event import Event
from models.suggestion import Suggestion


class TestSuggestEventMediaController(unittest2.TestCase):

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True)

        Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)

    def storeEvent(self):
        self.event = Event(
            id="2016nyny",
            event_type_enum=EventType.REGIONAL,
            name="NYC",
            event_short="NYC",
            year=2016,
        )
        self.event.put()

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/event/media', SuggestEventMediaController, 'suggest-event-media', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def getSuggestionForm(self, event_key):
        response = self.testapp.get('/suggest/event/media?event_key={}'.format(event_key))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_media', None)
        self.assertIsNotNone(form)
        return form

    def testLoginRedirect(self):
        response = self.testapp.get('/suggest/event/media?event_key=2016nyny')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def testNoParams(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/media', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def testSubmitEmptyForm(self):
        self.loginUser()
        self.storeEvent()
        form = self.getSuggestionForm('2016nyny')
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_url')

    def testBadEvent(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/media?event_key=2016nyny', status='4*')
        self.assertEqual(response.status_int, 404)

    def testSuggestMedia(self):
        self.loginUser()
        self.storeEvent()
        form = self.getSuggestionForm('2016nyny')
        form['media_url'] = 'https://www.youtube.com/watch?v=H-54KMwMKY0'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')

        suggestion = Suggestion.get_by_id('media_2016_event_2016nyny_youtube_H-54KMwMKY0')
        self.assertIsNotNone(suggestion)

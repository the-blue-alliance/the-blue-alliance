import json
import unittest2

from google.appengine.ext import testbed
from google.appengine.ext import ndb

from models.sitevar import Sitevar
from sitevars.google_analytics_id import GoogleAnalyticsID


class TestNotificationsEnable(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_default_sitevar(self):
        default_sitevar = GoogleAnalyticsID._default_sitevar()
        self.assertIsNotNone(default_sitevar)

        default_json = {'GOOGLE_ANALYTICS_ID': ''}
        self.assertEqual(default_sitevar.values_json, json.dumps(default_json))
        self.assertEqual(default_sitevar.contents, default_json)

    def test_google_analytics_id(self):
        self.assertEqual(GoogleAnalyticsID.google_analytics_id(), '')

    def test_google_analytics_id_set(self):
        test_id = 'abc'
        Sitevar.get_or_insert('google_analytics.id', values_json=json.dumps({'GOOGLE_ANALYTICS_ID': test_id}))
        self.assertEqual(GoogleAnalyticsID.google_analytics_id(), test_id)

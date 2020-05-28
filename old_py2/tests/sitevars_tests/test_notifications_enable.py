import json
import unittest2

from google.appengine.ext import testbed
from google.appengine.ext import ndb

from models.sitevar import Sitevar
from sitevars.notifications_enable import NotificationsEnable


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
        default_sitevar = NotificationsEnable._default_sitevar()
        self.assertIsNotNone(default_sitevar)
        self.assertEqual(default_sitevar.values_json, 'true')
        self.assertEqual(default_sitevar.contents, True)

    def test_notifications_enabled_insert(self):
        self.assertTrue(NotificationsEnable.notifications_enabled())

    def test_notifications_enabled_get(self):
        notifications = Sitevar.get_or_insert('notifications.enable', values_json=json.dumps(False))
        self.assertFalse(NotificationsEnable.notifications_enabled())

    def test_enable_notifications(self):
        self.assertTrue(NotificationsEnable.notifications_enabled())
        NotificationsEnable.enable_notifications(False)
        self.assertFalse(NotificationsEnable.notifications_enabled())
        NotificationsEnable.enable_notifications(True)
        self.assertTrue(NotificationsEnable.notifications_enabled())

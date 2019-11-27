import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.sitevar import Sitevar
from sitevars.website_blacklist import WebsiteBlacklist


class TestWebsiteBlacklist(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        Sitevar(id='website_blacklist', values_json=json.dumps({'websites': ['http://blacklist.com/']})).put()
        self.website_blacklist = WebsiteBlacklist()

    def tearDown(self):
        self.testbed.deactivate()

    def test_is_blacklisted(self):
        self.assertTrue(self.website_blacklist.is_blacklisted('http://blacklist.com/'))
        self.assertFalse(self.website_blacklist.is_blacklisted('https://www.thebluealliance.com/'))

    def test_blacklist(self):
        website = 'https://www.thebluealliance.com/'
        self.assertFalse(self.website_blacklist.is_blacklisted(website))
        self.website_blacklist.blacklist(website)
        self.assertTrue(self.website_blacklist.is_blacklisted(website))
        self.assertTrue(self.website_blacklist.is_blacklisted('http://blacklist.com/'))

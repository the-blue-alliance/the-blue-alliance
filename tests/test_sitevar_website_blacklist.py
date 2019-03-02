import json
import unittest2

from models.sitevar import Sitevar
from sitevars.website_blacklist import WebsiteBlacklist


class TestWebsiteBlacklist(unittest2.TestCase):

    def setUp(self):
        Sitevar(id='website_blacklist', values_json=json.dumps({'websites': ['http://blacklist.com/']})).put()
        self.website_blacklist = WebsiteBlacklist()

    def test_blacklist(self):
        self.assertTrue(self.website_blacklist.is_blacklisted('http://blacklist.com/'))
        self.assertFalse(self.website_blacklist.is_blacklisted('https://www.thebluealliance.com/'))

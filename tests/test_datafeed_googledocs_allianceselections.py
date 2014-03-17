import json
import unittest2

from google.appengine.ext import testbed

from datafeeds.datafeed_googledocs_allianceselections import DatafeedGoogleDocsAllianceSelection
from models.event import Event, EventType


class TestDatafeedGoogleDocsAllianceSelections(unittest2.TestCase):
    
    CASA = """{"1": {"declines": [], "picks": ["frc971", "frc1678", "frc766"]}, "2": {"declines": [], "picks": ["frc2085", "frc1671", "frc692"]}, "3": {"declines": [], "picks": ["frc2761", "frc100", "frc1662"]}, "4": {"declines": [], "picks": ["frc114", "frc2035", "frc115"]}, "5": {"declines": [], "picks": ["frc4159", "frc599", "frc3250"]}, "6": {"declines": [], "picks": ["frc1280", "frc4135", "frc701"]}, "7": {"declines": [], "picks": ["frc668", "frc1868", "frc2073"]}, "8": {"declines": [], "picks": ["frc1388", "frc2551", "frc2144"]}}"""

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.datafeed = DatafeedGoogleDocsAllianceSelection()

        # Create a stub 2014casa
        event = Event(
            id='2014casa',
            event_type_enum=EventType.REGIONAL,
            year=2014,
            event_short='casa'
        )
        event.put()

    def assertValidJSON(self, thing):
        try:
            json.loads(thing)
            self.assertTrue(True)
        except ValueError:
            self.assertTrue(False)

    def tearDown(self):
        self.testbed.deactivate()

    def test_run(self):
        events = self.datafeed.run(2014)
        casa = events[0]
        # Make sure we have the right event
        self.assertEqual(casa.event_short, 'casa')
        self.assertEqual(casa.year, 2014)
        # Now check the JSON we created
        self.assertValidJSON(casa.alliance_selections_json)
        self.assertEqual(casa.alliance_selections_json, self.CASA)



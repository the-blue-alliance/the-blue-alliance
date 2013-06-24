import datetime
import unittest2
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.usfirst_event_rankings_parser import UsfirstEventRankingsParser
from helpers.event_manipulator import EventManipulator
from models.event import Event

class TestEventManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        f1 = open('test_data/usfirst_html/usfirst_event_rankings_2012ct.html', 'r')
        good_rankings = UsfirstEventRankingsParser.parse(f1.read())
        
        f2 = open('test_data/usfirst_html/usfirst_event_rankings_2012ct_bad.html', 'r')
        bad_rankings = UsfirstEventRankingsParser.parse(f2.read())

        self.old_event = Event(
            id = "2011ct",
            end_date = datetime.datetime(2011, 4, 2, 0, 0),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime(2011, 3, 31, 0, 0),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr",
            rankings_json = json.dumps(good_rankings)
        )

        self.new_event = Event(
            id = "2011ct",
            end_date = datetime.datetime(2011, 4, 2, 0, 0),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime(2011, 3, 31, 0, 0),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr",

            oprs = [1.0, 2.0, 3.0],
            opr_teams = [177, 195, 233], # are these really stored as ints or strings? -gregmarra 20120922
            facebook_eid = "7",
            webcast_json = json.dumps([{'type': 'ustream', 'channel': 'foo'}]),
            rankings_json = json.dumps(bad_rankings)
        )
        
    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedEvent(self, event):
        self.assertOldEvent(event)
        self.assertEqual(event.oprs, [1, 2, 3])
        self.assertEqual(event.opr_teams, [177, 195, 233])
        self.assertEqual(event.facebook_eid, "7")
        self.assertEqual(event.webcast[0]['type'], 'ustream')
        self.assertEqual(event.webcast[0]['channel'], 'foo')
        self.assertEqual(event.rankings, [['Rank', 'Team', 'QS', 'HP', 'BP', 'TP', 'CP', 'Record (W-L-T)', 'DQ', 'Played'], ['1', '2168', '32.00', '147.00', '60.00', '208.00', '14', '9-1-0', '0', '10'], ['2', '118', '31.00', '168.00', '90.00', '231.00', '17', '7-3-0', '0', '10'], ['3', '177', '30.00', '177.00', '120.00', '151.00', '14', '8-2-0', '0', '10'], ['4', '195', '29.00', '116.00', '70.00', '190.00', '16', '6-3-1', '0', '10'], ['5', '237', '28.00', '120.00', '60.00', '123.00', '14', '7-3-0', '0', '10'], ['6', '1071', '28.00', '115.00', '120.00', '142.00', '10', '9-1-0', '0', '10'], ['7', '173', '28.00', '114.00', '110.00', '108.00', '14', '7-3-0', '0', '10'], ['8', '1073', '28.00', '110.00', '100.00', '152.00', '11', '8-1-1', '0', '10'], ['9', '694', '28.00', '78.00', '100.00', '140.00', '14', '7-3-0', '0', '10'], ['10', '558', '27.00', '152.00', '100.00', '145.00', '13', '7-3-0', '0', '10'], ['11', '175', '27.00', '141.00', '160.00', '117.00', '13', '7-3-0', '0', '10'], ['12', '181', '26.00', '151.00', '70.00', '95.00', '14', '6-4-0', '0', '10'], ['13', '176', '26.00', '120.00', '60.00', '90.00', '18', '4-6-0', '0', '10'], ['14', '1511', '26.00', '111.00', '80.00', '164.00', '14', '6-4-0', '0', '10'], ['15', '126', '26.00', '108.00', '70.00', '165.00', '14', '6-4-0', '0', '10'], ['16', '4122', '26.00', '92.00', '100.00', '78.00', '14', '6-4-0', '0', '10'], ['17', '869', '25.00', '68.00', '130.00', '75.00', '12', '6-3-1', '0', '10'], ['18', '3464', '24.00', '135.00', '80.00', '109.00', '14', '5-5-0', '0', '10'], ['19', '3467', '24.00', '101.00', '80.00', '123.00', '10', '7-3-0', '0', '10'], ['20', '3718', '24.00', '100.00', '60.00', '106.00', '12', '6-4-0', '0', '10'], ['21', '3461', '24.00', '79.00', '30.00', '94.00', '14', '5-5-0', '0', '10'], ['22', '4055', '24.00', '78.00', '80.00', '79.00', '16', '4-6-0', '0', '10'], ['23', '1922', '23.00', '114.00', '110.00', '151.00', '10', '6-3-1', '0', '10'], ['24', '95', '22.00', '120.00', '70.00', '123.00', '14', '4-6-0', '0', '10'], ['25', '1991', '22.00', '113.00', '100.00', '58.00', '12', '5-5-0', '0', '10'], ['26', '839', '22.00', '96.00', '110.00', '136.00', '10', '6-4-0', '0', '10'], ['27', '1099', '21.00', '126.00', '110.00', '97.00', '8', '6-3-1', '0', '10'], ['28', '230', '20.00', '143.00', '80.00', '104.00', '8', '6-4-0', '0', '10'], ['29', '3017', '20.00', '134.00', '50.00', '88.00', '12', '4-6-0', '0', '10'], ['30', '2067', '20.00', '128.00', '80.00', '122.00', '10', '5-5-0', '0', '10'], ['31', '250', '20.00', '118.00', '40.00', '99.00', '10', '5-5-0', '0', '10'], ['32', '155', '20.00', '100.00', '50.00', '74.00', '12', '4-6-0', '0', '10'], ['33', '236', '20.00', '99.00', '20.00', '126.00', '10', '5-5-0', '0', '10'], ['34', '1124', '20.00', '92.00', '80.00', '109.00', '8', '6-4-0', '0', '10'], ['35', '3146', '20.00', '81.00', '110.00', '81.00', '6', '7-3-0', '0', '10'], ['36', '663', '20.00', '71.00', '90.00', '90.00', '12', '4-6-0', '0', '10'], ['37', '1699', '20.00', '70.00', '80.00', '139.00', '12', '4-6-0', '0', '10'], ['38', '1027', '20.00', '53.00', '70.00', '97.00', '12', '4-6-0', '0', '10'], ['39', '20', '19.00', '79.00', '70.00', '106.00', '9', '5-5-0', '0', '10'], ['40', '3182', '18.00', '108.00', '60.00', '147.00', '8', '5-5-0', '0', '10'], ['41', '229', '18.00', '97.00', '40.00', '153.00', '10', '4-6-0', '0', '10'], ['42', '1665', '18.00', '95.00', '120.00', '106.00', '10', '4-6-0', '0', '10'], ['43', '228', '18.00', '81.00', '60.00', '163.00', '10', '4-6-0', '0', '10'], ['44', '178', '18.00', '81.00', '50.00', '58.00', '12', '3-7-0', '0', '10'], ['45', '1740', '18.00', '62.00', '20.00', '99.00', '8', '5-5-0', '0', '10'], ['46', '3634', '18.00', '54.00', '30.00', '105.00', '10', '4-6-0', '0', '10'], ['47', '2791', '18.00', '53.00', '100.00', '108.00', '10', '4-6-0', '0', '10'], ['48', '571', '18.00', '53.00', '70.00', '109.00', '10', '4-6-0', '0', '10'], ['49', '2170', '17.00', '89.00', '60.00', '103.00', '9', '4-5-0', '1', '10'], ['50', '1493', '16.00', '150.00', '60.00', '132.00', '6', '5-5-0', '0', '10'], ['51', '549', '16.00', '129.00', '100.00', '91.00', '6', '5-5-0', '0', '10'], ['52', '743', '16.00', '70.00', '30.00', '67.00', '10', '3-7-0', '0', '10'], ['53', '2836', '16.00', '64.00', '80.00', '126.00', '8', '4-6-0', '0', '10'], ['54', '999', '14.00', '114.00', '20.00', '79.00', '10', '2-8-0', '0', '10'], ['55', '3525', '14.00', '109.00', '40.00', '66.00', '6', '4-6-0', '0', '10'], ['56', '3104', '14.00', '92.00', '20.00', '80.00', '6', '4-6-0', '0', '10'], ['57', '3555', '14.00', '68.00', '60.00', '68.00', '8', '3-7-0', '0', '10'], ['58', '4134', '13.00', '96.00', '30.00', '80.00', '6', '3-6-1', '0', '10'], ['59', '1559', '12.00', '110.00', '10.00', '94.00', '8', '2-8-0', '0', '10'], ['60', '3719', '12.00', '97.00', '60.00', '95.00', '6', '3-7-0', '0', '10'], ['61', '3654', '12.00', '59.00', '20.00', '57.00', '8', '2-8-0', '0', '10'], ['62', '2785', '12.00', '41.00', '70.00', '96.00', '8', '2-8-0', '0', '10'], ['63', '1880', '10.00', '57.00', '40.00', '86.00', '6', '2-8-0', '0', '10'], ['64', '1784', '10.00', '44.00', '40.00', '60.00', '6', '2-7-0', '1', '10']])

    def assertOldEvent(self, event):
        self.assertEqual(event.key.id(), "2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type, Event.REGIONAL)
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(event.venue_address, "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")

    def test_createOrUpdate(self):
        EventManipulator.createOrUpdate(self.old_event)
        self.assertOldEvent(Event.get_by_id("2011ct"))
        EventManipulator.createOrUpdate(self.new_event)
        self.assertMergedEvent(Event.get_by_id("2011ct"))

    def test_findOrSpawn(self):
        self.old_event.put()
        self.assertMergedEvent(EventManipulator.findOrSpawn(self.new_event))

    def test_updateMerge(self):
        self.assertMergedEvent(EventManipulator.updateMerge(self.new_event, self.old_event))

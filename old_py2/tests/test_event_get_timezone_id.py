# import unittest2
#
# from google.appengine.ext import ndb
# from google.appengine.ext import testbed
#
# from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
# from helpers.location_helper import LocationHelper
#
#
# class TestEventGetTimezoneId(unittest2.TestCase):
#     def setUp(self):
#         self.testbed = testbed.Testbed()
#         self.testbed.activate()
#         self.testbed.init_urlfetch_stub()
#         self.testbed.init_datastore_v3_stub()
#         self.testbed.init_memcache_stub()
#         ndb.get_context().clear_cache()  # Prevent data from leaking between tests
#
#     def test_2012ct_no_location(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         event['location'] = None
#         self.assertEqual(LocationHelper.get_lat_lng(event['location']), None)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), None)
#
#     def test_2012ct_bad_location(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         event['location'] = "somewhere on mars"
#         self.assertEqual(LocationHelper.get_lat_lng(event['location']), None)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), None)
#
#     def test_2012ct(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 41.7658043, places=3)
#         self.assertAlmostEqual(location[1], -72.6733723, places=3)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/New_York')
#
#     def test_2013flbr(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2013flbr.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 26.1224386, places=6)
#         self.assertAlmostEqual(location[1], -80.13731740000001, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/New_York')
#
#     def test_2013casj(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2013casj.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 37.3382082, places=6)
#         self.assertAlmostEqual(location[1], -121.8863286, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/Los_Angeles')
#
#     def test_2001sj(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2001ca2.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 37.3382082, places=6)
#         self.assertAlmostEqual(location[1], -121.8863286, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/Los_Angeles')
#
#     def test_2005is(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2005is.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 32.7940463, places=6)
#         self.assertAlmostEqual(location[1], 34.989571, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'Asia/Jerusalem')
#
#     def test_2005or(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2005or.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 45.5122308, places=6)
#         self.assertAlmostEqual(location[1], -122.6587185, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/Los_Angeles')
#
#     def test_1997il(self):
#         with open('test_data/usfirst_html/usfirst_event_details_1997il.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 41.8781136, places=6)
#         self.assertAlmostEqual(location[1], -87.6297982, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/Chicago')
#
#     def test_2002sj(self):
#         with open('test_data/usfirst_html/usfirst_event_details_2002sj.html', 'r') as f:
#             event, _ = UsfirstEventDetailsParser.parse(f.read())
#
#         location = None
#         for _ in xrange(5):
#             location = LocationHelper.get_lat_lng(event['location'])
#             if location:
#                 break
#         self.assertAlmostEqual(location[0], 37.3382082, places=6)
#         self.assertAlmostEqual(location[1], -121.8863286, places=6)
#         self.assertEqual(LocationHelper.get_timezone_id(event['location']), 'America/Los_Angeles')

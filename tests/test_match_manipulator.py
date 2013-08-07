import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.match_manipulator import MatchManipulator
from models.event import Event
from models.match import Match


class TestMatchManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.event = Event(
          id="2012ct",
          event_short="ct",
          year=2012
        )

        self.old_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=self.event.key,
            game="frc_2012_rebr",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073']
        )

        self.new_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=self.event.key,
            game="frc_2012_rebr",
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073']
        )

    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedMatch(self, match):
        self.assertOldMatch(match)
        self.assertEqual(match.alliances_json, """{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""")

    def assertOldMatch(self, match):
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 1)
        self.assertEqual(match.team_key_names, [u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'])

    def test_createOrUpdate(self):
        MatchManipulator.createOrUpdate(self.old_match)

        self.assertOldMatch(Match.get_by_id("2012ct_qm1"))
        self.assertEqual(Match.get_by_id("2012ct_qm1").alliances_json, """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""")

        MatchManipulator.createOrUpdate(self.new_match)
        self.assertMergedMatch(Match.get_by_id("2012ct_qm1"))

    def test_findOrSpawn(self):
        self.old_match.put()
        self.assertMergedMatch(MatchManipulator.findOrSpawn(self.new_match))

    def test_updateMerge(self):
        self.assertMergedMatch(MatchManipulator.updateMerge(self.new_match, self.old_match))

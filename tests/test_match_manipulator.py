import json
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
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.event = Event(
            id="2012ct",
            event_short="ct",
            year=2012
        )

        self.old_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            score_breakdown_json=json.dumps({
                'red': {'auto': 20, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            }),
            comp_level="qm",
            event=self.event.key,
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=[u'P3C2BOtL7e8', u'tst1', u'tst2', u'tst3']
        )

        self.new_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
            score_breakdown_json=json.dumps({
                'red': {'auto': 80, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            }),
            comp_level="qm",
            event=self.event.key,
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=[u'TqY324xLU4s', u'tst1', u'tst3', u'tst4']
        )

    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedMatch(self, match, is_auto_union):
        self.assertOldMatch(match)
        self.assertEqual(match.alliances_json, """{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""")
        if is_auto_union:
            self.assertEqual(set(match.youtube_videos), {u'P3C2BOtL7e8', u'TqY324xLU4s', u'tst1', u'tst2', u'tst3', u'tst4'})
        else:
            self.assertEqual(match.youtube_videos, [u'TqY324xLU4s', u'tst1', u'tst3', u'tst4'])
        self.assertEqual(match.score_breakdown['red']['auto'], 80)

    def assertOldMatch(self, match):
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 1)
        self.assertEqual(match.team_key_names, [u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'])

    def test_createOrUpdate(self):
        MatchManipulator.createOrUpdate(self.old_match)

        self.assertOldMatch(Match.get_by_id("2012ct_qm1"))
        self.assertEqual(Match.get_by_id("2012ct_qm1").alliances_json, """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""")
        self.assertEqual(Match.get_by_id("2012ct_qm1").score_breakdown['red']['auto'], 20)

        MatchManipulator.createOrUpdate(self.new_match)
        self.assertMergedMatch(Match.get_by_id("2012ct_qm1"), True)

    def test_findOrSpawn(self):
        self.old_match.put()
        self.assertMergedMatch(MatchManipulator.findOrSpawn(self.new_match), True)

    def test_updateMerge(self):
        self.assertMergedMatch(MatchManipulator.updateMerge(self.new_match, self.old_match), True)

    def test_createOrUpdate_no_auto_union(self):
        MatchManipulator.createOrUpdate(self.old_match)

        self.assertOldMatch(Match.get_by_id("2012ct_qm1"))
        self.assertEqual(Match.get_by_id("2012ct_qm1").alliances_json, """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""")

        MatchManipulator.createOrUpdate(self.new_match, auto_union=False)
        self.assertMergedMatch(Match.get_by_id("2012ct_qm1"), False)

    def test_findOrSpawn_no_auto_union(self):
        self.old_match.put()
        self.assertMergedMatch(MatchManipulator.findOrSpawn(self.new_match, auto_union=False), False)

    def test_updateMerge_no_auto_union(self):
        self.assertMergedMatch(MatchManipulator.updateMerge(self.new_match, self.old_match, auto_union=False), False)

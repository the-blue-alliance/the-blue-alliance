import json
import unittest

import pytest
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.mark.usefixtures("ndb_context")
class TestMatchManipulator(unittest.TestCase):
    def setUp(self):
        self.event = Event(id="2012ct", event_short="ct", year=2012)

        self.old_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            score_breakdown_json=json.dumps(
                {
                    AllianceColor.RED: {
                        "auto": 20,
                        "assist": 40,
                        "truss+catch": 20,
                        "teleop_goal+foul": 20,
                    },
                    AllianceColor.BLUE: {
                        "auto": 40,
                        "assist": 60,
                        "truss+catch": 10,
                        "teleop_goal+foul": 40,
                    },
                }
            ),
            comp_level="qm",
            event=self.event.key,
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[
                u"frc69",
                u"frc571",
                u"frc176",
                u"frc3464",
                u"frc20",
                u"frc1073",
            ],
            youtube_videos=[u"P3C2BOtL7e8", u"tst1", u"tst2", u"tst3"],
        )

        self.new_match = Match(
            id="2012ct_qm1",
            alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
            score_breakdown_json=json.dumps(
                {
                    "red": {
                        "auto": 80,
                        "assist": 40,
                        "truss+catch": 20,
                        "teleop_goal+foul": 20,
                    },
                    "blue": {
                        "auto": 40,
                        "assist": 60,
                        "truss+catch": 10,
                        "teleop_goal+foul": 40,
                    },
                }
            ),
            comp_level="qm",
            event=self.event.key,
            year=2012,
            set_number=1,
            match_number=1,
            team_key_names=[
                u"frc69",
                u"frc571",
                u"frc176",
                u"frc3464",
                u"frc20",
                u"frc1073",
            ],
            youtube_videos=[u"TqY324xLU4s", u"tst1", u"tst3", u"tst4"],
        )

    def assertMergedMatch(self, match: Match, is_auto_union: bool) -> None:
        self.assertOldMatch(match)
        self.assertEqual(
            match.alliances_json,
            """{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        )
        if is_auto_union:
            self.assertEqual(
                set(match.youtube_videos),
                {u"P3C2BOtL7e8", u"TqY324xLU4s", u"tst1", u"tst2", u"tst3", u"tst4"},
            )
        else:
            self.assertEqual(
                match.youtube_videos, [u"TqY324xLU4s", u"tst1", u"tst3", u"tst4"]
            )
        self.assertEqual(
            none_throws(match.score_breakdown)[AllianceColor.RED]["auto"], 80
        )

    def assertOldMatch(self, match: Match) -> None:
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 1)
        self.assertEqual(
            match.team_key_names,
            [u"frc69", u"frc571", u"frc176", u"frc3464", u"frc20", u"frc1073"],
        )

    def test_createOrUpdate(self) -> None:
        MatchManipulator.createOrUpdate(self.old_match)

        match = Match.get_by_id("2012ct_qm1")
        self.assertIsNotNone(match)
        self.assertOldMatch(match)
        self.assertEqual(
            match.alliances_json,
            """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        )
        self.assertEqual(match.score_breakdown[AllianceColor.RED]["auto"], 20)

        MatchManipulator.createOrUpdate(self.new_match)
        self.assertMergedMatch(Match.get_by_id("2012ct_qm1"), True)

    def test_findOrSpawn(self) -> None:
        self.old_match.put()
        self.assertMergedMatch(MatchManipulator.findOrSpawn(self.new_match), True)

    def test_updateMerge(self) -> None:
        self.assertMergedMatch(
            MatchManipulator.updateMerge(self.new_match, self.old_match), True
        )

    def test_createOrUpdate_no_auto_union(self) -> None:
        MatchManipulator.createOrUpdate(self.old_match)

        self.assertOldMatch(Match.get_by_id("2012ct_qm1"))
        self.assertEqual(
            Match.get_by_id("2012ct_qm1").alliances_json,
            """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        )

        MatchManipulator.createOrUpdate(self.new_match, auto_union=False)
        self.assertMergedMatch(Match.get_by_id("2012ct_qm1"), False)

    def test_findOrSpawn_no_auto_union(self) -> None:
        self.old_match.put()
        self.assertMergedMatch(
            MatchManipulator.findOrSpawn(self.new_match, auto_union=False), False
        )

    def test_updateMerge_no_auto_union(self) -> None:
        self.assertMergedMatch(
            MatchManipulator.updateMerge(
                self.new_match, self.old_match, auto_union=False
            ),
            False,
        )

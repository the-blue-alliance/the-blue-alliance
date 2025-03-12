import json
import unittest
from unittest import mock
from unittest.mock import patch

import pytest
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
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
                "frc69",
                "frc571",
                "frc176",
                "frc3464",
                "frc20",
                "frc1073",
            ],
            youtube_videos=["P3C2BOtL7e8", "tst1", "tst2", "tst3"],
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
                "frc69",
                "frc571",
                "frc176",
                "frc3464",
                "frc20",
                "frc1073",
            ],
            youtube_videos=["TqY324xLU4s", "tst1", "tst3", "tst4"],
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
                {"P3C2BOtL7e8", "TqY324xLU4s", "tst1", "tst2", "tst3", "tst4"},
            )
        else:
            self.assertEqual(
                match.youtube_videos, ["TqY324xLU4s", "tst1", "tst3", "tst4"]
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
            ["frc69", "frc571", "frc176", "frc3464", "frc20", "frc1073"],
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
        self.assertEqual(
            none_throws(match.score_breakdown)[AllianceColor.RED]["auto"], 20
        )

        MatchManipulator.createOrUpdate(self.new_match)
        self.assertMergedMatch(none_throws(Match.get_by_id("2012ct_qm1")), True)

    def test_findOrSpawn(self) -> None:
        self.old_match.put()
        self.assertMergedMatch(MatchManipulator.findOrSpawn(self.new_match), True)

    def test_updateMerge(self) -> None:
        self.assertMergedMatch(
            MatchManipulator.updateMerge(self.new_match, self.old_match), True
        )

    def test_updateMerge_addVideo(self) -> None:
        self.old_match.youtube_videos = []
        result = MatchManipulator.updateMerge(self.new_match, self.old_match)
        self.assertTrue("_video_added" in result._updated_attrs)

    def test_createOrUpdate_no_auto_union(self) -> None:
        MatchManipulator.createOrUpdate(self.old_match)

        self.assertOldMatch(none_throws(Match.get_by_id("2012ct_qm1")))
        self.assertEqual(
            none_throws(Match.get_by_id("2012ct_qm1")).alliances_json,
            """{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        )

        MatchManipulator.createOrUpdate(self.new_match, auto_union=False)
        self.assertMergedMatch(none_throws(Match.get_by_id("2012ct_qm1")), False)

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


@mock.patch.object(FirebasePusher, "update_match")
def test_updateHook(mock_firebase, ndb_context, taskqueue_stub) -> None:
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator._run_post_update_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    mock_firebase.assert_called_once_with(test_match, set())


@mock.patch.object(FirebasePusher, "update_match")
def test_updateHook_firebaseThrows(mock_firebase, ndb_context, taskqueue_stub) -> None:
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    mock_firebase.side_effect = Exception
    MatchManipulator._run_post_update_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)


@mock.patch.object(taskqueue, "add")
def test_updateHook_taskqueueThrows(
    mock_taskqueue, ndb_context, taskqueue_stub
) -> None:
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    test_match._updated_attrs = {"alliances_json"}
    mock_taskqueue.side_effect = Exception
    MatchManipulator._run_post_update_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)


def test_updateHook_enqueueStats(ndb_context, taskqueue_stub) -> None:
    Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    ).put()
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(test_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    stats_tasks = taskqueue_stub.get_filtered_tasks(queue_names="stats")
    assert len(stats_tasks) > 0

    tasks_urls = [t.url for t in stats_tasks]
    assert "/tasks/math/do/playoff_advancement_update/2012ct" in tasks_urls
    assert "/tasks/math/do/event_team_status/2012ct" in tasks_urls
    assert "/tasks/math/do/district_points_calc/2012ct" in tasks_urls


def test_updateHook_enqueueStatsRegionalChampsPoints(
    ndb_context, taskqueue_stub
) -> None:
    Event(
        id="2025ct", event_short="ct", year=2025, event_type_enum=EventType.REGIONAL
    ).put()
    test_match = Match(
        id="2025ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2025ct"),
        year=2025,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(test_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    stats_tasks = taskqueue_stub.get_filtered_tasks(queue_names="stats")
    assert len(stats_tasks) > 0

    tasks_urls = [t.url for t in stats_tasks]
    assert "/tasks/math/do/playoff_advancement_update/2025ct" in tasks_urls
    assert "/tasks/math/do/event_team_status/2025ct" in tasks_urls
    assert "/tasks/math/do/district_points_calc/2025ct" in tasks_urls
    assert "/tasks/math/do/regional_champs_pool_points_calc/2025ct" in tasks_urls


@mock.patch.object(FirebasePusher, "delete_match")
def test_deleteHook(mock_firebase, ndb_context, taskqueue_stub) -> None:
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator._run_post_delete_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    mock_firebase.assert_called_once_with(test_match)


@mock.patch.object(FirebasePusher, "delete_match")
def test_deleteHook_firebaseThrows(mock_firebase, ndb_context, taskqueue_stub) -> None:
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    mock_firebase.side_effect = Exception
    MatchManipulator._run_post_delete_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)


def test_postUpdateHook_notifications(ndb_context, taskqueue_stub) -> None:
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
        push_sent=False,
    )
    MatchManipulator.createOrUpdate(test_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        with patch.object(Event, "now", return_value=True):
            run_from_task(task)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    assert len(tasks) == 1
    task = tasks[0]
    assert task.name == "2012ct_qm1_match_score"

    test_match = none_throws(Match.get_by_id("2012ct_qm1"))
    assert test_match.push_sent


def test_postUpdateHook_notification_pushSent(ndb_context, taskqueue_stub) -> None:
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
        push_sent=True,
    )
    MatchManipulator.createOrUpdate(test_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        with patch.object(Event, "now", return_value=True):
            run_from_task(task)

    tasks = taskqueue_stub.get_filtered_tasks(
        name="2012ct_qm1_match_score", queue_names="push-notifications"
    )
    assert len(tasks) == 0

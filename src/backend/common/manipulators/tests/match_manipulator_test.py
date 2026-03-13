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
def test_updateHook_corrupted_null_event(
    mock_firebase, ndb_context, taskqueue_stub
) -> None:
    """Nullapalooza (#9236): corrupted Match with event=None should be skipped."""
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    # Simulate corrupted entity — NDB required=True only validates on put()
    test_match.event = None
    MatchManipulator._run_post_update_hook([test_match])

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    mock_firebase.assert_not_called()


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


def test_postUpdateHook_notification_pushSent(ndb_context, taskqueue_stub) -> None:
    """push_sent is now used for upcoming match notifications, not match_score.
    A match with push_sent=True should still get a match_score notification."""
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
    assert len(tasks) == 1


def test_postUpdateHook_webhook_notification_on_breakdown_update(
    ndb_context, taskqueue_stub
) -> None:
    """When score_breakdown_json changes on a played match without alliances_json
    changing, a webhook-only match score notification should be enqueued."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create initial match with scores
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    test_match.put()

    # Now update the match with a score breakdown
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        score_breakdown_json=json.dumps(
            {
                "red": {"auto": 20, "teleop": 54},
                "blue": {"auto": 30, "teleop": 27},
            }
        ),
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(updated_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        with patch.object(Event, "now", return_value=True):
            run_from_task(task)

    # Should have a webhook-only notification (unnamed task), NOT a named match_score task
    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    assert len(push_tasks) == 1
    # The webhook-only task should NOT have the named match_score task name
    named_tasks = taskqueue_stub.get_filtered_tasks(
        name="2012ct_qm1_match_score", queue_names="push-notifications"
    )
    assert len(named_tasks) == 0


def test_postUpdateHook_webhook_on_breakdown_regardless_of_push_sent(
    ndb_context, taskqueue_stub
) -> None:
    """When score_breakdown_json changes without alliances_json changing,
    a webhook-only notification should be sent regardless of push_sent value."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create initial match with scores and push_sent=False
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
    test_match.put()

    # Update with score breakdown only (alliances_json is unchanged)
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        score_breakdown_json=json.dumps(
            {
                "red": {"auto": 20, "teleop": 54},
                "blue": {"auto": 30, "teleop": 27},
            }
        ),
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
        push_sent=False,
    )
    MatchManipulator.createOrUpdate(updated_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        with patch.object(Event, "now", return_value=True):
            run_from_task(task)

    # Breakdown-only update should now send webhook-only notification
    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    assert len(push_tasks) == 1


def test_postUpdateHook_no_webhook_on_breakdown_when_event_not_now(
    ndb_context, taskqueue_stub
) -> None:
    """No webhook-only notification should be sent for events that are not currently happening."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create initial match with scores
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    test_match.put()

    # Update with score breakdown
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        score_breakdown_json=json.dumps(
            {
                "red": {"auto": 20, "teleop": 54},
                "blue": {"auto": 30, "teleop": 27},
            }
        ),
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(updated_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    for task in tasks:
        # event.now is False by default (no patch)
        run_from_task(task)

    # No push-notifications tasks should be created since event is not "now"
    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    assert len(push_tasks) == 0


def test_postUpdateHook_no_duplicate_webhook_during_countdown(
    ndb_context, taskqueue_stub
) -> None:
    """Scores arrive first, then breakdown arrives during the delay window.
    The initial match_score task (named) should be present, plus a webhook-only
    task for the breakdown.  The initial task will read the latest data
    (including breakdown) when it executes."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Step 1: Create a match with scores (no breakdown) → triggers delayed notification
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

    # Run the post-update-hook task (enqueues the delayed push-notification)
    hook_tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(hook_tasks) == 1
    with patch.object(Event, "now", return_value=True):
        run_from_task(hook_tasks[0])

    # The delayed match_score task should be enqueued
    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    assert len(push_tasks) == 1
    assert push_tasks[0].name == "2012ct_qm1_match_score"

    # Step 2: Score breakdown arrives during the delay window
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 57, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        score_breakdown_json=json.dumps(
            {
                "red": {"auto": 20, "teleop": 54},
                "blue": {"auto": 30, "teleop": 27},
            }
        ),
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(updated_match)

    # Run the second post-update-hook
    hook_tasks_2 = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(hook_tasks_2) == 2  # original + new
    with patch.object(Event, "now", return_value=True):
        run_from_task(hook_tasks_2[1])

    # The breakdown-only update adds a webhook-only task (alliances_json
    # didn't change, only score_breakdown_json did).  The original named
    # match_score task is still present and will include the breakdown
    # when it runs because it reads fresh data from Datastore.
    push_tasks_after = taskqueue_stub.get_filtered_tasks(
        queue_names="push-notifications"
    )
    assert len(push_tasks_after) == 2


def test_postUpdateHook_schedule_notification_for_unplayed_match(
    ndb_context, taskqueue_stub
) -> None:
    """When an unplayed match is updated with a schedule-affecting change,
    event_schedule and schedule_upcoming_matches notifications should fire."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create an unplayed match (scores are -1)
    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    test_match.put()

    # Update alliances_json (still unplayed – teams change but scores stay -1)
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc254", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(updated_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    with patch.object(Event, "now", return_value=True):
        run_from_task(tasks[0])

    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    task_names = [t.name for t in push_tasks]
    assert "2012ct_event_schedule" in task_names
    assert "2012ct_schedule_upcoming_matches" in task_names


def test_postUpdateHook_no_schedule_notification_for_played_match(
    ndb_context, taskqueue_stub
) -> None:
    """When a played match has its alliances_json updated (e.g. score correction),
    schedule notifications must NOT be sent – only match_score should fire."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create a played match (scores > -1)
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
    test_match.put()

    # Score correction – alliances_json changes but match is still played
    updated_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": 60, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": 74, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
        push_sent=False,
    )
    MatchManipulator.createOrUpdate(updated_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    with patch.object(Event, "now", return_value=True):
        run_from_task(tasks[0])

    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    task_names = [t.name for t in push_tasks]
    # Should get a match_score notification, NOT schedule notifications
    assert "2012ct_qm1_match_score" in task_names
    assert "2012ct_event_schedule" not in task_names
    assert "2012ct_schedule_upcoming_matches" not in task_names


def test_postUpdateHook_new_unplayed_match_sends_schedule_notification(
    ndb_context, taskqueue_stub
) -> None:
    """A brand-new unplayed match should trigger schedule notifications."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    test_match = Match(
        id="2012ct_qm1",
        alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
        comp_level="qm",
        event=ndb.Key(Event, "2012ct"),
        year=2012,
        set_number=1,
        match_number=1,
    )
    MatchManipulator.createOrUpdate(test_match)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1
    with patch.object(Event, "now", return_value=True):
        run_from_task(tasks[0])

    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    task_names = [t.name for t in push_tasks]
    assert "2012ct_event_schedule" in task_names
    assert "2012ct_schedule_upcoming_matches" in task_names


def test_postUpdateHook_new_played_match_no_schedule_notification(
    ndb_context, taskqueue_stub
) -> None:
    """A brand-new match that already has scores should NOT trigger schedule
    notifications – it should trigger match_score instead."""
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
    with patch.object(Event, "now", return_value=True):
        run_from_task(tasks[0])

    push_tasks = taskqueue_stub.get_filtered_tasks(queue_names="push-notifications")
    task_names = [t.name for t in push_tasks]
    assert "2012ct_qm1_match_score" in task_names
    assert "2012ct_event_schedule" not in task_names
    assert "2012ct_schedule_upcoming_matches" not in task_names

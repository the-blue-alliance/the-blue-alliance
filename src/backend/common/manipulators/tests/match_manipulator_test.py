import json
import unittest
from unittest import mock
from unittest.mock import patch

import pytest
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.manipulators.match_manipulator import (
    MATCH_SCORE_DELAY_SECONDS,
    MatchManipulator,
    MatchPostUpdateHooks,
)
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

    # push_sent is not set until the notification task actually executes
    # (see TBANSHelper.match_score), so it should still be False here.
    test_match = none_throws(Match.get_by_id("2012ct_qm1"))
    assert not test_match.push_sent


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


def test_postUpdateHook_webhook_notification_on_breakdown_update(
    ndb_context, taskqueue_stub
) -> None:
    """When score_breakdown_json changes on a match that already had push_sent=True,
    a webhook-only match score notification should be enqueued."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create initial match with scores and push_sent=True (simulates initial notification already sent)
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
        push_sent=True,
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

    # push_sent should still be True (not reset)
    test_match = none_throws(Match.get_by_id("2012ct_qm1"))
    assert test_match.push_sent


def test_postUpdateHook_no_webhook_on_breakdown_when_not_push_sent(
    ndb_context, taskqueue_stub
) -> None:
    """When score_breakdown_json changes but push_sent is False, only the normal
    match_score notification should be sent (not a separate webhook-only one)."""
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

    # Only score_breakdown_json changed, and push_sent is False, so no webhook-only notification
    # There should be no push-notifications tasks
    named_tasks = taskqueue_stub.get_filtered_tasks(
        name="2012ct_qm1_match_score", queue_names="push-notifications"
    )
    assert len(named_tasks) == 0


def test_postUpdateHook_no_webhook_on_breakdown_when_event_not_now(
    ndb_context, taskqueue_stub
) -> None:
    """No webhook-only notification should be sent for events that are not currently happening."""
    event = Event(
        id="2012ct", event_short="ct", year=2012, event_type_enum=EventType.REGIONAL
    )
    event.put()

    # Create initial match with scores and push_sent=True
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
        push_sent=True,
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
    """Scores arrive first (with countdown delay), then breakdown arrives during
    the delay window.  Only one push-notification task should be enqueued — the
    original delayed match_score — and no webhook-only duplicate."""
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
        push_sent=False,
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

    # push_sent is NOT yet True — it will be set when the task actually executes
    db_match = none_throws(Match.get_by_id("2012ct_qm1"))
    assert not db_match.push_sent

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
        push_sent=False,
    )
    MatchManipulator.createOrUpdate(updated_match)

    # Run the second post-update-hook
    hook_tasks_2 = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(hook_tasks_2) == 2  # original + new
    with patch.object(Event, "now", return_value=True):
        run_from_task(hook_tasks_2[1])

    # No additional push-notification tasks should have been enqueued.
    # The webhook-only branch requires push_sent=True which is still False,
    # and alliances_json didn't change so the initial branch also doesn't fire.
    push_tasks_after = taskqueue_stub.get_filtered_tasks(
        queue_names="push-notifications"
    )
    assert len(push_tasks_after) == 1  # Still just the original delayed task


class TestMatchScoreNotificationCountdown:
    """Tests for MatchPostUpdateHooks.match_score_notification_countdown."""

    @pytest.fixture
    def official_event(self, ndb_context) -> Event:
        event = Event(
            id="2024ct",
            event_short="ct",
            year=2024,
            event_type_enum=EventType.REGIONAL,
            official=True,
        )
        event.put()
        return event

    @pytest.fixture
    def offseason_event(self, ndb_context) -> Event:
        event = Event(
            id="2024osc",
            event_short="osc",
            year=2024,
            event_type_enum=EventType.OFFSEASON,
            official=False,
        )
        event.put()
        return event

    @pytest.fixture
    def qual_match_no_breakdown(self, ndb_context) -> Match:
        return Match(
            id="2024ct_qm1",
            comp_level="qm",
            event=ndb.Key(Event, "2024ct"),
            year=2024,
            set_number=1,
            match_number=1,
            alliances_json="""{"blue": {"score": 50, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 60, "teams": ["frc4", "frc5", "frc6"]}}""",
        )

    @pytest.fixture
    def qual_match_with_breakdown(self, ndb_context) -> Match:
        return Match(
            id="2024ct_qm1",
            comp_level="qm",
            event=ndb.Key(Event, "2024ct"),
            year=2024,
            set_number=1,
            match_number=1,
            alliances_json="""{"blue": {"score": 50, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 60, "teams": ["frc4", "frc5", "frc6"]}}""",
            score_breakdown_json=json.dumps(
                {"red": {"auto": 20}, "blue": {"auto": 30}}
            ),
        )

    @pytest.fixture
    def playoff_match_no_breakdown(self, ndb_context) -> Match:
        return Match(
            id="2024ct_sf1m1",
            comp_level="sf",
            event=ndb.Key(Event, "2024ct"),
            year=2024,
            set_number=1,
            match_number=1,
            alliances_json="""{"blue": {"score": 50, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 60, "teams": ["frc4", "frc5", "frc6"]}}""",
        )

    def test_returns_zero_when_breakdown_present(
        self, qual_match_with_breakdown: Match, official_event: Event
    ) -> None:
        countdown = MatchPostUpdateHooks.match_score_notification_countdown(
            qual_match_with_breakdown, official_event
        )
        assert countdown == 0

    def test_returns_delay_for_sync_enabled_qual(
        self, qual_match_no_breakdown: Match, official_event: Event
    ) -> None:
        with patch.object(Event, "is_sync_enabled", return_value=True) as mock_sync:
            countdown = MatchPostUpdateHooks.match_score_notification_countdown(
                qual_match_no_breakdown, official_event
            )
            assert countdown == MATCH_SCORE_DELAY_SECONDS
            mock_sync.assert_called_once_with(EventSyncType.EVENT_QUAL_MATCHES)

    def test_returns_delay_for_sync_enabled_playoff(
        self, playoff_match_no_breakdown: Match, official_event: Event
    ) -> None:
        with patch.object(Event, "is_sync_enabled", return_value=True) as mock_sync:
            countdown = MatchPostUpdateHooks.match_score_notification_countdown(
                playoff_match_no_breakdown, official_event
            )
            assert countdown == MATCH_SCORE_DELAY_SECONDS
            mock_sync.assert_called_once_with(EventSyncType.EVENT_PLAYOFF_MATCHES)

    def test_returns_zero_for_sync_disabled(
        self, qual_match_no_breakdown: Match, official_event: Event
    ) -> None:
        with patch.object(Event, "is_sync_enabled", return_value=False):
            countdown = MatchPostUpdateHooks.match_score_notification_countdown(
                qual_match_no_breakdown, official_event
            )
            assert countdown == 0

    def test_returns_zero_for_offseason_event(self, ndb_context) -> None:
        offseason_event = Event(
            id="2024osc",
            event_short="osc",
            year=2024,
            event_type_enum=EventType.OFFSEASON,
            official=False,
        )
        offseason_event.put()
        match = Match(
            id="2024osc_qm1",
            comp_level="qm",
            event=ndb.Key(Event, "2024osc"),
            year=2024,
            set_number=1,
            match_number=1,
            alliances_json="""{"blue": {"score": 50, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": 60, "teams": ["frc4", "frc5", "frc6"]}}""",
        )
        # is_sync_enabled returns False for non-official events
        countdown = MatchPostUpdateHooks.match_score_notification_countdown(
            match, offseason_event
        )
        assert countdown == 0

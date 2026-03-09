import json
import unittest
from typing import Optional
from unittest.mock import patch

import pytest
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from pyre_extensions import none_throws

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
class TestAwardManipulator(unittest.TestCase):
    taskqueue_stub: Optional[testbed.taskqueue_stub.TaskQueueServiceStub] = None

    @pytest.fixture(autouse=True)
    def store_taskqueue_stub(self, taskqueue_stub):
        self.taskqueue_stub = taskqueue_stub

    def setUp(self):
        self.event = Event(
            id="2013casj",
            event_short="casj",
            year=2013,
            event_type_enum=EventType.REGIONAL,
        )
        self.event.put()

        self.event2025 = Event(
            id="2025casj",
            event_short="casj",
            year=2025,
            event_type_enum=EventType.REGIONAL,
        )
        self.event2025.put()

        self.old_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str="Regional Winner",
            award_type_enum=AwardType.WINNER,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc111"), ndb.Key(Team, "frc234")],
            recipient_json_list=[
                json.dumps({"team_number": 111, "awardee": None}),
                json.dumps({"team_number": 234, "awardee": None}),
            ],
        )

        self.new_award = Award(
            id="2013casj_1",
            name_str="Regional Champion",
            award_type_enum=AwardType.WINNER,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc359")],
            recipient_json_list=[json.dumps({"team_number": 359, "awardee": None})],
        )

        self.new_award2025 = Award(
            id="2025casj_1",
            name_str="Regional Champion",
            award_type_enum=AwardType.WINNER,
            year=2025,
            event=self.event2025.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc359")],
            recipient_json_list=[json.dumps({"team_number": 359, "awardee": None})],
        )

    def assertMergedAward(self, award, is_auto_union):
        self.assertEqual(award.name_str, "Regional Champion")
        self.assertEqual(award.award_type_enum, AwardType.WINNER)
        self.assertEqual(award.year, 2013)
        self.assertEqual(award.event, self.event.key)
        self.assertEqual(award.event_type_enum, EventType.REGIONAL)
        if is_auto_union:
            self.assertEqual(
                set(award.team_list),
                {
                    ndb.Key(Team, "frc111"),
                    ndb.Key(Team, "frc234"),
                    ndb.Key(Team, "frc359"),
                },
            )
            self.assertEqual(len(award.recipient_json_list), 3)
            for r in award.recipient_json_list:
                self.assertTrue(
                    json.loads(r)
                    in [
                        {"team_number": 111, "awardee": None},
                        {"team_number": 234, "awardee": None},
                        {"team_number": 359, "awardee": None},
                    ]
                )
        else:
            self.assertEqual(set(award.team_list), {ndb.Key(Team, "frc359")})
            self.assertEqual(len(award.recipient_json_list), 1)
            for r in award.recipient_json_list:
                self.assertTrue(
                    json.loads(r) in [{"team_number": 359, "awardee": None}]
                )

    def assertOldAward(self, award):
        self.assertEqual(award.name_str, "Regional Winner")
        self.assertEqual(award.award_type_enum, AwardType.WINNER)
        self.assertEqual(award.year, 2013)
        self.assertEqual(award.event, self.event.key)
        self.assertEqual(award.event_type_enum, EventType.REGIONAL)
        self.assertEqual(
            set(award.team_list), {ndb.Key(Team, "frc111"), ndb.Key(Team, "frc234")}
        )
        self.assertEqual(len(award.recipient_json_list), 2)
        for r in award.recipient_json_list:
            self.assertTrue(
                json.loads(r)
                in [
                    {"team_number": 111, "awardee": None},
                    {"team_number": 234, "awardee": None},
                ]
            )

    def test_createOrUpdateupdate(self):
        AwardManipulator.createOrUpdate(self.old_award)
        self.assertOldAward(Award.get_by_id("2013casj_1"))

        AwardManipulator.createOrUpdate(self.new_award)
        self.assertMergedAward(Award.get_by_id("2013casj_1"), True)

    def test_findOrSpawn(self):
        self.old_award.put()
        self.assertMergedAward(AwardManipulator.findOrSpawn(self.new_award), True)

    def test_updateMerge(self):
        self.assertMergedAward(
            AwardManipulator.updateMerge(self.new_award, self.old_award), True
        )

    def test_createOrUpdate_no_auto_union(self):
        AwardManipulator.createOrUpdate(self.old_award)
        self.assertOldAward(Award.get_by_id("2013casj_1"))

        AwardManipulator.createOrUpdate(self.new_award, auto_union=False)
        self.assertMergedAward(Award.get_by_id("2013casj_1"), False)

    def test_findOrSpawn_no_auto_union(self):
        self.old_award.put()
        self.assertMergedAward(
            AwardManipulator.findOrSpawn(self.new_award, auto_union=False), False
        )

    def test_updateMerge_no_auto_union(self):
        self.assertMergedAward(
            AwardManipulator.updateMerge(
                self.new_award, self.old_award, auto_union=False
            ),
            False,
        )

    def test_postUpdateHook_districtPoints(self):
        AwardManipulator.createOrUpdate(self.new_award)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        # Ensure we have a district_points_calc test enqueued
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="default"
        )
        assert len(tasks) == 1

        task = tasks[0]
        assert task.url == "/tasks/math/do/district_points_calc/2013casj"

    def test_postUpdateHook_regionalChampsPoints(self):
        AwardManipulator.createOrUpdate(self.new_award2025)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1
        for task in tasks:
            run_from_task(task)

        # Ensure we have a district_points_calc test enqueued
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="default"
        )

        task_urls = {t.url for t in tasks}
        assert "/tasks/math/do/regional_champs_pool_points_calc/2025casj" in task_urls

    def test_postUpdateHook_notifications(self):
        import datetime

        # Setup our event to be "now"
        self.event.start_date = datetime.datetime.now()
        self.event.end_date = self.event.start_date + datetime.timedelta(days=1)

        AwardManipulator.createOrUpdate(self.new_award)

        # But the update hook should have skipped adding it
        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1

        for task in tasks:
            run_from_task(task)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="push-notifications"
        )
        assert len(tasks) == 1

    def test_postUpdateHook_notifications_second_update(self):
        """A second award update should still enqueue a notification task."""
        import datetime

        self.event.start_date = datetime.datetime.now()
        self.event.end_date = self.event.start_date + datetime.timedelta(days=1)

        # First award creation
        AwardManipulator.createOrUpdate(self.new_award)
        hook_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(hook_tasks) == 1
        run_from_task(hook_tasks[0])

        first_push_count = len(
            none_throws(self.taskqueue_stub).get_filtered_tasks(
                queue_names="push-notifications"
            )
        )
        assert first_push_count == 1

        # Second award creation for the same event
        second_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.FINALIST),
            name_str="Regional Finalist",
            award_type_enum=AwardType.FINALIST,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc111")],
            recipient_json_list=[json.dumps({"team_number": 111, "awardee": None})],
        )
        AwardManipulator.createOrUpdate(second_award)
        hook_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        # Run only the second hook task
        run_from_task(hook_tasks[-1])

        # Should now have TWO push-notification tasks (not blocked by tombstone)
        push_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="push-notifications"
        )
        assert len(push_tasks) == 2

    def test_postUpdateHook_notifications_passes_new_team_keys(self):
        """New award team keys are passed through to TBANSHelper.awards()."""
        import datetime

        self.event.start_date = datetime.datetime.now()
        self.event.end_date = self.event.start_date + datetime.timedelta(days=1)

        AwardManipulator.createOrUpdate(self.new_award)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        for task in tasks:
            run_from_task(task)

        # Run the push-notification task and verify args
        push_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="push-notifications"
        )
        assert len(push_tasks) == 1

        with patch.object(TBANSHelper, "awards") as mock_awards:
            for task in push_tasks:
                run_from_task(task)

            mock_awards.assert_called_once()
            call_kwargs = mock_awards.call_args
            # event_key is the first positional arg
            assert call_kwargs[0][0] == "2013casj"
            # new_award_team_keys should contain the team from the new award
            assert call_kwargs[1]["new_award_team_keys"] == {"frc359"}

    def test_postUpdateHook_notifications_updated_award_empty_new_team_keys(self):
        """Updated (not new) awards pass empty new_award_team_keys."""
        import datetime

        self.event.start_date = datetime.datetime.now()
        self.event.end_date = self.event.start_date + datetime.timedelta(days=1)

        # First, create the award
        AwardManipulator.createOrUpdate(self.new_award)
        # Drain post-update-hooks and push-notifications
        for task in none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        ):
            run_from_task(task)

        # Now update the same award (change name)
        updated_award = Award(
            id="2013casj_1",
            name_str="Regional Winner",
            award_type_enum=AwardType.WINNER,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc359")],
            recipient_json_list=[json.dumps({"team_number": 359, "awardee": None})],
        )
        AwardManipulator.createOrUpdate(updated_award)

        # Run the second post-update-hook
        all_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        # Run only the latest hook (second one)
        run_from_task(all_tasks[-1])

        # Get push-notification tasks (there should be 2 now)
        push_tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="push-notifications"
        )
        # Run the latest push task and verify args
        with patch.object(TBANSHelper, "awards") as mock_awards:
            run_from_task(push_tasks[-1])

            mock_awards.assert_called_once()
            call_kwargs = mock_awards.call_args
            assert call_kwargs[0][0] == "2013casj"
            # Not a new award, so new_award_team_keys should be empty
            assert call_kwargs[1]["new_award_team_keys"] == set()

    def test_postUpdateHook_notifications_notWithinADay(self):
        AwardManipulator.createOrUpdate(self.new_award)

        tasks = none_throws(self.taskqueue_stub).get_filtered_tasks(
            queue_names="post-update-hooks"
        )
        assert len(tasks) == 1

        for task in tasks:
            with patch.object(TBANSHelper, "awards") as mock_awards:
                run_from_task(task)

        # Event is not configured to be within a day - skip it
        mock_awards.assert_not_called()

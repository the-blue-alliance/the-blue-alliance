import logging
from typing import List

from google.appengine.api import taskqueue
from google.appengine.ext import deferred

from backend.common.cache_clearing import get_affected_queries
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.match import Match


class MatchManipulator(ManipulatorBase[Match]):
    """
    Handle Match database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.match_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls, new_model: Match, old_model: Match, auto_union: bool = True
    ) -> Match:
        # Lets postUpdateHook know if videos went from 0 to >0
        added_video = not old_model.has_video and new_model.has_video

        cls._update_attrs(new_model, old_model, auto_union)

        if added_video:
            old_model._updated_attrs.add("_video_added")

        return old_model


@MatchManipulator.register_post_delete_hook
def match_post_delete_hook(deleted_models: List[Match]) -> None:
    for match in deleted_models:
        try:
            FirebasePusher.delete_match(match)
        except Exception:
            logging.warning("Firebase delete_match failed!")


@MatchManipulator.register_post_update_hook
def match_post_update_hook(updated_models: List[TUpdatedModel[Match]]) -> None:
    affected_stats_event_keys = set()
    for updated_model in updated_models:
        MatchPostUpdateHooks.firebase_update(updated_model)
        MatchPostUpdateHooks.enqueue_stats(updated_model)

        # Only attrs that affect stats
        if (
            updated_model.is_new
            or set(["alliances_json", "score_breakdown_json"]).intersection(
                set(updated_model.updated_attrs)
            )
            != set()
        ):
            affected_stats_event_keys.add(updated_model.model.event.id())

    # Enqueue statistics
    for event_key in affected_stats_event_keys:
        # Enqueue task to calculate matchstats
        try:
            taskqueue.add(
                url=f"/tasks/math/do/event_matchstats/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="default",
            )
        except Exception:
            logging.exception(f"Error enqueuing event_matchstats for {event_key}")

    # Dispatch push notifications
    unplayed_match_events = []
    for updated_match in updated_models:
        match = updated_match.model
        event = match.event.get()
        # Only continue if the event is currently happening
        if event and event.now:
            if match.has_been_played and not match.push_sent:
                if (
                    updated_match.is_new
                    or "alliances_json" in updated_match.updated_attrs
                ):
                    # Catch TaskAlreadyExistsError + TombstonedTaskError
                    try:
                        deferred.defer(
                            TBANSHelper.match_score,
                            match,
                            _name=f"{match.key_name}_match_score",
                            _target="py3-tasks-io",
                            _queue="push-notifications",
                            _url="/_ah/queue/deferred_notification_send",
                        )
                        # Update score sent boolean on Match object to make sure we only send a notification once
                        match.push_sent = True
                        MatchManipulator.createOrUpdate(match, run_post_update_hook=False)
                    except Exception:
                        pass
            else:
                if updated_match.is_new or (
                    set(["alliances_json", "time", "time_string"]).intersection(
                        set(updated_match.updated_attrs)
                    )
                    != set()
                ):
                    # The match has not been played and we're changing a property that affects the event's schedule
                    # So send a schedule update notification for the parent event
                    if event not in unplayed_match_events:
                        unplayed_match_events.append(event)

        # Try to send video notifications
        if "_video_added" in updated_match.updated_attrs:
            # Catch TaskAlreadyExistsError + TombstonedTaskError
            try:
                deferred.defer(
                    TBANSHelper.match_video,
                    match,
                    _name=f"{match.key_name}_match_video",
                    _target="py3-tasks-io",
                    _queue="push-notifications",
                    _url="/_ah/queue/deferred_notification_send",
                )
            except Exception:
                pass

    """
    If we have an unplayed match during an event within a day, send out a schedule update notification
    """
    for event in unplayed_match_events:
        # Catch TaskAlreadyExistsError + TombstonedTaskError
        try:
            deferred.defer(
                TBANSHelper.event_schedule,
                event,
                _name=f"{event.key_name}_event_schedule",
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send",
            )
        except Exception:
            pass

        # Catch TaskAlreadyExistsError + TombstonedTaskError
        try:
            deferred.defer(
                TBANSHelper.schedule_upcoming_matches,
                event,
                _name=f"{event.key_name}_schedule_upcoming_matches",
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send",
            )
        except Exception:
            pass


class MatchPostUpdateHooks:
    """
    Since there are so many match update hooks, we can port them individually here
    and do a better job of batching so we don't have to iterate the same list a bunch
    """

    @staticmethod
    def firebase_update(model: TUpdatedModel[Match]) -> None:
        """
        Enqueue firebase push
        """
        try:
            FirebasePusher.update_match(model.model, model.updated_attrs)
        except Exception:
            logging.exception("Firebase update_match failed!")

    @staticmethod
    def enqueue_stats(model: TUpdatedModel[Match]) -> None:
        # Enqueue task to calculate district points
        event_key = model.model.event_key_name
        try:
            taskqueue.add(
                url=f"/tasks/math/do/district_points_calc/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="default",
                countdown=300,  # Wait ~5m so cache clearing can run before we attempt to recalculate district points
            )
        except Exception:
            logging.exception(f"Error enqueuing district_points_calc for {event_key}")

        # Enqueue task to calculate event team status
        try:
            taskqueue.add(
                url=f"/tasks/math/do/event_team_status/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="default",
            )
        except Exception:
            logging.exception(f"Error enqueuing event_team_status for {event_key}")

        # Enqueue updating playoff advancement
        try:
            taskqueue.add(
                url=f"/tasks/math/do/playoff_advancement_update/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="default",
            )
        except Exception:
            logging.exception(f"Error enqueuing advancement update for {event_key}")

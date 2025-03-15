import logging
from typing import List, Optional, Set, TYPE_CHECKING

from google.appengine.api import taskqueue
from pyre_extensions import none_throws

from backend.common.cache_clearing import get_affected_queries
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    EventNexusQueueStatusMemcache,
)
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.keys import EventKey
from backend.common.models.match import Match

if TYPE_CHECKING:
    from backend.common.models.event import Event


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
        cls,
        new_model: Match,
        old_model: Match,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Match:
        # Lets postUpdateHook know if videos went from 0 to >0
        added_video = not old_model.has_video and new_model.has_video

        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)

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
    affected_stats_event_keys: Set[EventKey] = set()
    affected_stats_events: List[Event] = []

    all_affected_event_keys: Set[EventKey] = {
        none_throws(m.model.event.string_id())
        for m in updated_models
        if m.model.event.string_id() is not None
    }
    event_nexus_status = {
        ek: EventNexusQueueStatusMemcache(ek).get() for ek in all_affected_event_keys
    }

    for updated_model in updated_models:
        event_key: EventKey = none_throws(updated_model.model.event.string_id())
        MatchPostUpdateHooks.firebase_update(
            updated_model, event_nexus_status.get(event_key)
        )

        # Only attrs that affect stats
        if (
            updated_model.is_new
            or set(["alliances_json", "score_breakdown_json"]).intersection(
                set(updated_model.updated_attrs)
            )
            != set()
        ):
            event = updated_model.model.event.get()
            if event_key and event and event_key not in affected_stats_event_keys:
                affected_stats_event_keys.add(event_key)
                affected_stats_events.append(event)

    # Enqueue statistics
    for event in affected_stats_events:
        MatchPostUpdateHooks.enqueue_stats(event)

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
                        defer_safe(
                            TBANSHelper.match_score,
                            match,
                            _name=f"{match.key_name}_match_score",
                            _target="py3-tasks-io",
                            _queue="push-notifications",
                            _url="/_ah/queue/deferred_notification_send",
                        )
                        # Update score sent boolean on Match object to make sure we only send a notification once
                        match.push_sent = True
                        MatchManipulator.createOrUpdate(
                            match, run_post_update_hook=False
                        )
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
                defer_safe(
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
            defer_safe(
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
            defer_safe(
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
    def firebase_update(
        model: TUpdatedModel[Match], nexus_status: Optional[EventQueueStatus]
    ) -> None:
        """
        Enqueue firebase push
        """
        try:
            FirebasePusher.update_match(model.model, model.updated_attrs, nexus_status)
        except Exception:
            logging.exception("Firebase update_match failed!")

    @staticmethod
    def enqueue_stats(event: "Event") -> None:
        event_key = event.key_name
        # Enqueue task to calculate district points
        try:
            taskqueue.add(
                url=f"/tasks/math/do/district_points_calc/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="stats",
                countdown=90,  # Wait ~1.5m so cache clearing can run before we attempt to recalculate district points
            )
        except Exception:
            logging.exception(f"Error enqueuing district_points_calc for {event_key}")

        if (
            SeasonHelper.is_valid_regional_pool_year(event.year)
            and event.event_type_enum == EventType.REGIONAL
        ):
            try:
                taskqueue.add(
                    url=f"/tasks/math/do/regional_champs_pool_points_calc/{event_key}",
                    method="GET",
                    target="py3-tasks-io",
                    queue_name="stats",
                    countdown=90,  # Wait ~1.5m so cache clearing can run before we attempt to recalculate district points
                )
            except Exception:
                logging.exception(
                    f"Error enqueuing regional_champs_pool_calc for {event_key}"
                )

        # Enqueue task to calculate event team status
        try:
            taskqueue.add(
                url=f"/tasks/math/do/event_team_status/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="stats",
                countdown=90,
            )
        except Exception:
            logging.exception(f"Error enqueuing event_team_status for {event_key}")

        # Enqueue updating playoff advancement
        try:
            taskqueue.add(
                url=f"/tasks/math/do/playoff_advancement_update/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="stats",
                countdown=90,
            )
        except Exception:
            logging.exception(f"Error enqueuing advancement update for {event_key}")

        # Enqueue task to calculate matchstats
        try:
            taskqueue.add(
                url=f"/tasks/math/do/event_matchstats/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="stats",
                countdown=90,  # Wait ~1.5m so cache clearing can run before we attempt to recalculate matchstats
            )
        except Exception:
            logging.exception(f"Error enqueuing event_matchstats for {event_key}")

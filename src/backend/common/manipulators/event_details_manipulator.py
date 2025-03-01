import logging
from typing import List

from google.appengine.api import taskqueue

from backend.common.cache_clearing import get_affected_queries
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails


class EventDetailsManipulator(ManipulatorBase[EventDetails]):
    """
    Handle EventDetails database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.event_details_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: EventDetails,
        old_model: EventDetails,
        auto_union: bool = True,
    ) -> EventDetails:
        cls._update_attrs(new_model, old_model, auto_union)
        return old_model


@EventDetailsManipulator.register_post_update_hook
def event_details_post_update_hook(
    updated_models: List[TUpdatedModel[EventDetails]],
) -> None:
    for updated_model in updated_models:
        # Enqueue task to calculate district points
        event_key = updated_model.model.key_name
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

        event = Event.get_by_id(event_key)
        if (
            event
            and event.within_a_day
            and "alliance_selections" in updated_model.updated_attrs
        ):
            # Catch TaskAlreadyExistsError + TombstonedTaskError
            try:
                defer_safe(
                    TBANSHelper.alliance_selection,
                    event,
                    _name=f"{event.key_name}_alliance_selection",
                    _target="py3-tasks-io",
                    _queue="push-notifications",
                    _url="/_ah/queue/deferred_notification_send",
                )
            except Exception:
                pass

        if (
            event
            and SeasonHelper.is_valid_regional_pool_year(event.year)
            and event.event_type_enum == EventType.REGIONAL
        ):
            try:
                taskqueue.add(
                    url=f"/tasks/math/do/regional_champs_pool_points_calc/{event_key}",
                    method="GET",
                    target="py3-tasks-io",
                    queue_name="default",
                    countdown=300,  # Wait ~5m so cache clearing can run before we attempt to recalculate district points
                )
            except Exception:
                logging.exception(
                    f"Error enqueuing regional_champs_points_calc for {event_key}"
                )


"""ndb
    @classmethod
    def postUpdateHook(cls, event_details_list, updated_attr_list, is_new_list):
        '''
        To run after models have been updated
        '''
        for (event_details, updated_attrs) in zip(event_details_list, updated_attr_list):
            try:
                FirebasePusher.update_event_details(event_details)
            except Exception:
                logging.warning("Firebase update_event_details failed!")
"""

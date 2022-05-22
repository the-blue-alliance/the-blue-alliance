import logging
import traceback
from typing import List

from google.appengine.api import taskqueue

from backend.common.cache_clearing import get_affected_queries
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
        event_key = updated_model.model.key_name

        # Enqueue task to calculate district points
        taskqueue.add(
            url=f"/tasks/math/do/district_points_calc/{event_key}",
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
            countdown=300,  # Wait ~5m so cache clearing can run before we attempt to recalculate district points
        )

        # Enqueue task to calculate event team status
        taskqueue.add(
            url=f"/tasks/math/do/event_team_status/{event_key}",
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

        event = Event.get_by_id(event_key)
        if event and event.within_a_day and "alliance_selections" in updated_model.updated_attrs:
            taskqueue.add(
                url=f"/tbans/alliance_selections/{event_key}",
                method="GET",
                target="py3-tasks-io",
                queue_name="default",
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

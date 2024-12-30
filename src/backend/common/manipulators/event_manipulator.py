import json
import logging
from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.helpers.location_helper import LocationHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event import Event


class EventManipulator(ManipulatorBase[Event]):
    """
    Handle Event database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.event_updated(affected_refs)

    """
    @classmethod
    def postDeleteHook(cls, events):
        '''
        To run after the event has been deleted.
        '''
        for event in events:
            SearchHelper.remove_event_location_index(event)
    """

    @classmethod
    def updateMerge(
        cls,
        new_model: Event,
        old_model: Event,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Event:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)

        # Special case to handle webcast_json
        if not auto_union and new_model.webcast != old_model.webcast:
            old_model.webcast_json = new_model.webcast_json
            old_model._webcast = None
            old_model._dirty = True
        else:
            if new_model.webcast:
                old_webcasts = old_model.webcast
                if old_webcasts:
                    for webcast in new_model.webcast:
                        if webcast in old_webcasts:
                            continue
                        else:
                            old_webcasts.append(webcast)
                            old_model.webcast_json = json.dumps(old_webcasts)
                else:
                    old_model.webcast_json = new_model.webcast_json
                old_model._dirty = True

        return old_model


@EventManipulator.register_post_update_hook
def event_post_update_hook(updated_models: List[TUpdatedModel[Event]]) -> None:
    events = []
    for updated in updated_models:
        event = updated.model
        try:
            LocationHelper.update_event_location(event)
        except Exception as e:
            logging.error(
                "update_event_location for {} errored!".format(event.key.id())
            )
            logging.exception(e)

        try:
            if event.normalized_location and event.normalized_location.lat_lng:
                timezone_id = LocationHelper.get_timezone_id(
                    None, lat_lng=event.normalized_location.lat_lng
                )
                if not timezone_id:
                    logging.warning(
                        "Timezone update for event {} failed!".format(event.key_name)
                    )
                else:
                    event.timezone_id = timezone_id
            else:
                logging.warning(
                    "No Lat/Lng to update timezone_id for event {}!".format(
                        event.key_name
                    )
                )
        except Exception as e:
            logging.error("Timezone update for {} errored!".format(event.key.id()))
            logging.exception(e)

        """
        try:
            SearchHelper.update_event_location_index(event)
        except Exception, e:
            logging.error("update_event_location_index for {} errored!".format(event.key.id()))
            logging.exception(e)
        """

        events.append(event)

    EventManipulator.createOrUpdate(events, run_post_update_hook=False)

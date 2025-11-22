import json
import logging
from typing import List

from backend.common.cache_clearing import get_affected_queries
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
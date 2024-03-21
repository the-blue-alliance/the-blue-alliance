import json
from typing import List, Set

from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.cache_clearing import get_affected_queries
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.award import Award
from backend.common.models.cached_model import TAffectedReferences


class AwardManipulator(ManipulatorBase[Award]):
    """
    Handle Award database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.award_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls, new_model: Award, old_model: Award, auto_union: bool = True
    ) -> Award:
        auto_union_list_attrs = {
            "team_list",
            "recipient_json_list",
        }

        json_list_attrs = {"recipient_json_list"}

        cls._update_attrs(new_model, old_model, auto_union)

        for attr in auto_union_list_attrs:
            # JSON equaltiy comparison is not deterministic
            if attr in json_list_attrs:
                old_list = [json.loads(j) for j in getattr(old_model, attr)]
                new_list = [json.loads(j) for j in getattr(new_model, attr)]
            else:
                old_list = getattr(old_model, attr)
                new_list = getattr(new_model, attr)

            is_changed = old_list != new_list
            if auto_union:
                for item in new_list:
                    if item not in old_list:
                        old_list.append(item)
                        old_model._dirty = True
            else:
                old_list = new_list

            # Turn dicts back to JSON
            if attr in json_list_attrs:
                merged_list = [json.dumps(d) for d in old_list]
            else:
                merged_list = old_list

            setattr(old_model, attr, merged_list)
            old_model._dirty |= is_changed

        return old_model


@AwardManipulator.register_post_update_hook
def award_post_update_hook(updated_models: List[TUpdatedModel[Award]]) -> None:
    event_keys: Set[ndb.Key] = set()
    for updated_award in updated_models:
        event_keys.add(none_throws(updated_award.model.event))

    for event_key in event_keys:
        # Enqueue task to calculate district points
        taskqueue.add(
            url=f"/tasks/math/do/district_points_calc/{event_key.string_id()}",
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
            countdown=300,  # Wait ~5m so cache clearing can run before we attempt to recalculate district points
        )

        # Send push notifications if the awards post was within +/- 1 day of the Event
        event = event_key.get()
        if event and event.within_a_day:
            # Catch TaskAlreadyExistsError + TombstonedTaskError
            try:
                deferred.defer(
                    TBANSHelper.awards,
                    event,
                    _name=f"{event.key_name}_awards",
                    _target="py3-tasks-io",
                    _queue="push-notifications",
                    _url="/_ah/queue/deferred_notification_send",
                )
            except Exception:
                pass

from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.tbans_helper import TBANSHelper
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


class EventTeamManipulator(ManipulatorBase[EventTeam]):
    """
    Handle EventTeam database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.eventteam_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_model: EventTeam,
        old_model: EventTeam,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> EventTeam:
        """
        Update and return EventTeams.
        """
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
    

def notify_team_changes(updated_models: List[EventTeam], removed: bool) -> None:
    events = set()
    
    for updated_model in updated_models:
        events.add(updated_model.event.id())
    
    for event in events:
        
        try:
            defer_safe(
               TBANSHelper.event_teams,
                event,
                added_teams=[model.team.get() for model in updated_models if model.event.id() == event and not removed],
                removed_teams=[model.team.get() for model in updated_models if model.event.id() == event and removed],
                _target="py3-tasks-io",
                _queue="push-notifications",
                _url="/_ah/queue/deferred_notification_send", 
            )
        except Exception:
            pass

@EventTeamManipulator.register_post_update_hook
def notify_additions(updated_models: List[TUpdatedModel[EventTeam]]) -> None:
    event_teams = [updated_model.model for updated_model in updated_models]
    notify_team_changes(event_teams, False)

@EventTeamManipulator.register_post_delete_hook
def notify_removals(update_models: List[EventTeam]) -> None:
    notify_team_changes(update_models, True)

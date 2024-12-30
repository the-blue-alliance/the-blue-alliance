from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.team import Team


class TeamManipulator(ManipulatorBase[Team]):
    """
    Handle Team database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.team_updated(affected_refs)

    """
    @classmethod
    def postDeleteHook(cls, teams):
        # To run after the team has been deleted.
        for team in teams:
            SearchHelper.remove_team_location_index(team)

    @classmethod
    def postUpdateHook(cls, teams, updated_attr_list, is_new_list):
        # To run after models have been updated
        for (team, updated_attrs) in zip(teams, updated_attr_list):
            if 'city' in updated_attrs or 'state_prov' in updated_attrs or \
                    'country' in updated_attrs or 'postalcode' in updated_attrs:
                try:
                    LocationHelper.update_team_location(team)
                except Exception, e:
                    logging.error("update_team_location for {} errored!".format(team.key.id()))
                    logging.exception(e)

                try:
                    SearchHelper.update_team_location_index(team)
                except Exception, e:
                    logging.error("update_team_location_index for {} errored!".format(team.key.id()))
                    logging.exception(e)
        cls.createOrUpdate(teams, run_post_update_hook=False)
    """

    @classmethod
    def updateMerge(
        cls,
        new_model: Team,
        old_model: Team,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> Team:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)

        # Take the new tpid and tpid_year iff the year is newer than or equal to the old one
        if (
            new_model.first_tpid_year is not None
            and new_model.first_tpid_year >= old_model.first_tpid_year
        ):
            old_model.first_tpid_year = new_model.first_tpid_year
            old_model.first_tpid = new_model.first_tpid
            old_model._dirty = True

        return old_model

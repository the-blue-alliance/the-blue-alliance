import logging

from google.appengine.api import search

from helpers.cache_clearer import CacheClearer
from helpers.location_helper import LocationHelper
from helpers.manipulator_base import ManipulatorBase
from helpers.search_helper import SearchHelper


class TeamManipulator(ManipulatorBase):
    """
    Handle Team database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_team_cache_keys_and_controllers(affected_refs)

    @classmethod
    def postDeleteHook(cls, teams):
        '''
        To run after the team has been deleted.
        '''
        for team in teams:
            SearchHelper.remove_team_location_index(team)

    @classmethod
    def postUpdateHook(cls, teams, updated_attr_list, is_new_list):
        """
        To run after models have been updated
        """
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

    @classmethod
    def updateMerge(self, new_team, old_team, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "city",
            "state_prov",
            "country",
            "postalcode",
            "normalized_location",  # Overwrite whole thing as one
            "name",
            "nickname",
            "school_name",
            "home_cmp",
            "website",
            "rookie_year",
            "motto",
        ]

        for attr in attrs:
            if getattr(new_team, attr) is not None:
                if getattr(new_team, attr) != getattr(old_team, attr):
                    setattr(old_team, attr, getattr(new_team, attr))
                    old_team.dirty = True

        # Take the new tpid and tpid_year iff the year is newer than or equal to the old one
        if (new_team.first_tpid_year is not None and new_team.first_tpid_year >= old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
            old_team.dirty = True

        return old_team

from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.district_team import DistrictTeam


class DistrictTeamManipulator(ManipulatorBase[DistrictTeam]):
    """
    Handle DistrictTeam database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.districtteam_updated(affected_refs)

    """
    @classmethod
    def postUpdateHook(cls, district_teams, updated_attr_list, is_new_list):
        '''
        To run after a district team has been updated.
        '''
        for (district_team, updated_attrs) in zip(district_teams, updated_attr_list):
            # Enqueue task to calculate district rankings
            try:
                taskqueue.add(
                    url='/tasks/math/do/district_rankings_calc/{}'.format(district_team.district_key.id()),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing district_rankings_calc for {}".format(district_team.district_key.id()))
                logging.error(traceback.format_exc())
    """

    @classmethod
    def updateMerge(
        cls,
        new_model: DistrictTeam,
        old_model: DistrictTeam,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> DistrictTeam:
        """
        Update and return DistrictTeams
        """
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model

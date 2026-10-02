from typing import Type
from unittest.mock import Mock

import pytest

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.manipulators.nexus_event_details_manipulator import (
    NexusEventDetailsManipulator,
)
from backend.common.manipulators.regional_champs_pool_manipulator import (
    RegionalChampsPoolManipulator,
)
from backend.common.manipulators.robot_manipulator import RobotManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator


@pytest.mark.parametrize(
    "manipulator, affected_queries_fn",
    [
        (AwardManipulator, "award_updated"),
        (DistrictManipulator, "district_updated"),
        (DistrictTeamManipulator, "districtteam_updated"),
        (EventDetailsManipulator, "event_details_updated"),
        (EventManipulator, "event_updated"),
        (EventTeamManipulator, "eventteam_updated"),
        (MatchManipulator, "match_updated"),
        (MediaManipulator, "media_updated"),
        (RegionalChampsPoolManipulator, "regional_champs_pool_updated"),
        (RobotManipulator, "robot_updated"),
        (TeamManipulator, "team_updated"),
    ],
)
def test_getCacheKeysAndQueries_delegates(
    monkeypatch: pytest.MonkeyPatch,
    manipulator: Type[ManipulatorBase],
    affected_queries_fn: str,
) -> None:
    sentinel = [("cache_key", Mock())]
    mock_fn = Mock(return_value=sentinel)
    monkeypatch.setattr(get_affected_queries, affected_queries_fn, mock_fn)
    affected_refs = {"key": {"frc254"}}

    assert manipulator.getCacheKeysAndQueries(affected_refs) is sentinel
    mock_fn.assert_called_once_with(affected_refs)


def test_nexus_event_details_has_no_cached_queries() -> None:
    assert NexusEventDetailsManipulator.getCacheKeysAndQueries({}) == []

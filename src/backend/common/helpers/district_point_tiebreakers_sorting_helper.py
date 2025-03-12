from typing import List, Tuple

from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
)
from backend.common.models.keys import TeamKey


class DistrictPointTiebreakersSortingHelper:

    @classmethod
    def sorted_points(
        cls, event_points: EventDistrictPoints
    ) -> List[Tuple[TeamKey, TeamAtEventDistrictPoints]]:
        return sorted(
            event_points["points"].items(),
            key=lambda team_and_points: [
                -team_and_points[1]["total"],
                -team_and_points[1]["elim_points"],
                -team_and_points[1]["alliance_points"],
                -team_and_points[1]["qual_points"],
            ]
            + [
                -score
                for score in event_points["tiebreakers"]
                .get(team_and_points[0], {})
                .get("highest_qual_scores", [])
            ],
        )

from dataclasses import dataclass
from typing import cast, Dict, List, Tuple

from backend.common.frc_api.types import (
    DistrictRankingListModelV2,
    DistrictRankingTeamModelV2,
)
from backend.common.models.district_advancement import (
    ApiDistrictRankingTeamData,
    DistrictAdvancement,
)
from backend.common.models.keys import TeamKey
from backend.tasks_io.datafeeds.parsers.parser_paginated import ParserPaginated


@dataclass
class TParsedDistrictRankings:
    advancement: DistrictAdvancement
    adjustments: Dict[TeamKey, int]
    api_team_data: Dict[TeamKey, ApiDistrictRankingTeamData]


class FMSAPIDistrictRankingsParser(
    ParserPaginated[DistrictRankingListModelV2, TParsedDistrictRankings]
):
    def parse(
        self, response: DistrictRankingListModelV2
    ) -> Tuple[TParsedDistrictRankings, bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        district_ranks: DistrictAdvancement = {}
        adjustments: Dict[TeamKey, int] = {}
        api_team_data: Dict[TeamKey, ApiDistrictRankingTeamData] = {}

        api_ranks = cast(
            List[DistrictRankingTeamModelV2], response.get("districtRanks") or []
        )
        for ranking in api_ranks:
            team_key = f"frc{ranking["teamNumber"]}"
            district_ranks[team_key] = {
                "dcmp": ranking["qualifiedDistrictCmp"],
                "cmp": ranking["qualifiedFirstCmp"],
            }

            if adjust := ranking.get("adjustmentPoints"):
                adjustments[team_key] = adjust

            api_team_data[team_key] = ApiDistrictRankingTeamData(
                rank=ranking["rank"],
                total_points=ranking["totalPoints"],
                team_age_points=ranking["teamAgePoints"],
                event1_code=ranking.get("event1Code"),
                event1_points=(
                    int(p) if (p := ranking.get("event1Points")) is not None else None
                ),
                event2_code=ranking.get("event2Code"),
                event2_points=(
                    int(p) if (p := ranking.get("event2Points")) is not None else None
                ),
                district_cmp_code=ranking.get("districtCmpCode"),
                district_cmp_points=(
                    int(p)
                    if (p := ranking.get("districtCmpPoints")) is not None
                    else None
                ),
            )

        return (
            TParsedDistrictRankings(
                advancement=district_ranks,
                adjustments=adjustments,
                api_team_data=api_team_data,
            ),
            (current_page < total_pages),
        )

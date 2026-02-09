from dataclasses import dataclass
from typing import Dict, Tuple

from backend.common.frc_api.types import (
    DistrictRankingListModelV2,
    DistrictRankingTeamModelV2,
)
from backend.common.models.district_advancement import DistrictAdvancement
from backend.common.models.keys import TeamKey
from backend.tasks_io.datafeeds.parsers.parser_paginated import ParserPaginated


@dataclass
class TParsedDistrictAdvancement:
    advancement: DistrictAdvancement
    adjustments: Dict[TeamKey, int]


class FMSAPIDistrictRankingsParser(
    ParserPaginated[DistrictRankingListModelV2, TParsedDistrictAdvancement]
):
    def parse(
        self, response: DistrictRankingListModelV2
    ) -> Tuple[TParsedDistrictAdvancement, bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        district_ranks: DistrictAdvancement = {}
        adjustments: Dict[TeamKey, int] = {}

        api_ranks: list[DistrictRankingTeamModelV2] = response["DistrictRanks"] or []
        for ranking in api_ranks:
            team_key = f"frc{ranking["teamNumber"]}"
            district_ranks[team_key] = {
                "dcmp": ranking["qualifiedDistrictCmp"],
                "cmp": ranking["qualifiedFirstCmp"],
            }

            if adjust := ranking.get("adjustmentPoints"):
                adjustments[team_key] = adjust

        return (
            TParsedDistrictAdvancement(
                advancement=district_ranks,
                adjustments=adjustments,
            ),
            (current_page < total_pages),
        )

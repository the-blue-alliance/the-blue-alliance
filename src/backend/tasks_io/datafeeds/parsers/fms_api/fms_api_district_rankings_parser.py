from dataclasses import dataclass
from typing import Any, Dict, Tuple

from backend.common.models.district_advancement import DistrictAdvancement
from backend.common.models.keys import TeamKey
from backend.tasks_io.datafeeds.parsers.json.parser_paginated_json import (
    ParserPaginatedJSON,
)


@dataclass
class TParsedDistrictAdvancement:
    advancement: DistrictAdvancement
    adjustments: Dict[TeamKey, int]


class FMSAPIDistrictRankingsParser(ParserPaginatedJSON[TParsedDistrictAdvancement]):
    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[TParsedDistrictAdvancement, bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        district_ranks: DistrictAdvancement = {}
        adjustments: Dict[TeamKey, int] = {}

        for ranking in response["districtRanks"]:
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

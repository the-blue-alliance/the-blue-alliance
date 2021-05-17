from typing import Any, Dict, Optional, Tuple

from backend.common.models.district_advancement import DistrictAdvancement
from backend.tasks_io.datafeeds.parsers.json.parser_paginated_json import (
    ParserPaginatedJSON,
)


class FMSAPIDistrictRankingsParser(ParserPaginatedJSON[DistrictAdvancement]):
    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[Optional[DistrictAdvancement], bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        district_ranks: DistrictAdvancement = {}

        for ranking in response["districtRanks"]:
            district_ranks["frc{}".format(ranking["teamNumber"])] = {
                "dcmp": ranking["qualifiedDistrictCmp"],
                "cmp": ranking["qualifiedFirstCmp"],
            }

        return (
            district_ranks if district_ranks else None,
            (current_page < total_pages),
        )

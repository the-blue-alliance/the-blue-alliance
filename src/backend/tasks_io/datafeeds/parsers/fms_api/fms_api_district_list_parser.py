from typing import List

from pyre_extensions import none_throws

from backend.common.frc_api.types import (
    SeasonDistrictListModelV2,
    SeasonDistrictModelV2,
)
from backend.common.models.district import District
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class FMSAPIDistrictListParser(ParserBase[SeasonDistrictListModelV2, List[District]]):
    def __init__(self, season: int) -> None:
        self.season = season

    def parse(self, response: SeasonDistrictListModelV2) -> List[District]:
        districts = []

        api_districts: list[SeasonDistrictModelV2] = response["districts"] or []
        for district in api_districts:
            district_code = none_throws(district["code"]).lower()
            district_key = District.render_key_name(self.season, district_code)
            districts.append(
                District(
                    id=district_key,
                    abbreviation=district_code,
                    year=self.season,
                    display_name=district["name"],
                )
            )

        return districts

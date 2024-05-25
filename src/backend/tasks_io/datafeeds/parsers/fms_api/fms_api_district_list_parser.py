from typing import Any, Dict, List, Optional

from backend.common.models.district import District
from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


class FMSAPIDistrictListParser(ParserJSON[List[District]]):
    def __init__(self, season: int) -> None:
        self.season = season

    def parse(self, response: Dict[str, Any]) -> Optional[List[District]]:
        districts = []

        for district in response["districts"]:
            district_code = district["code"].lower()
            district_key = District.render_key_name(self.season, district_code)
            districts.append(
                District(
                    id=district_key,
                    abbreviation=district_code,
                    year=self.season,
                    display_name=district["name"],
                )
            )

        return districts if districts else None

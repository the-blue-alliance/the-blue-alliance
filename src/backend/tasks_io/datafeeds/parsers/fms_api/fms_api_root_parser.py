from typing import Any, Dict

from pyre_extensions import safe_cast
from typing_extensions import TypedDict

from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


class RootInfo(TypedDict):
    currentSeason: int
    maxSeason: int
    name: str
    apiVersion: str
    status: str


class FMSAPIRootParser(ParserJSON[RootInfo]):
    def parse(self, response: Dict[str, Any]) -> RootInfo:
        return safe_cast(RootInfo, response)

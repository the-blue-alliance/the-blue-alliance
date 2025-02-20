from typing import Any, cast, Dict

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
        return cast(RootInfo, response)

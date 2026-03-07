from typing import cast

from typing_extensions import TypedDict

from backend.common.frc_api.types import ApiIndexModelV2
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class RootInfo(TypedDict):
    currentSeason: int
    maxSeason: int
    name: str
    apiVersion: str
    status: str


class FMSAPIRootParser(ParserBase[ApiIndexModelV2, RootInfo]):
    def parse(self, response: ApiIndexModelV2) -> RootInfo:
        return cast(RootInfo, response)

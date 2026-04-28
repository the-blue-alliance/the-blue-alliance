from backend.common.datafeeds.parsers.parser_base import ParserBase
from backend.common.nexus_api.types import PitMap


class NexusAPIEventDetailsParser(ParserBase[PitMap, PitMap]):
    def parse(self, response: PitMap) -> PitMap:
        if not isinstance(response, dict):
            return {}

        return response

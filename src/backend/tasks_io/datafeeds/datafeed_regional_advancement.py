import logging
from typing import Any, Generator, Optional

from backend.common.models.keys import Year
from backend.common.profiler import Span
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase, TParsedResponse
from backend.tasks_io.datafeeds.parsers.ra.regional_advancement_parser import (
    RegionalAdvancementParser,
    TParsedRegionalAdvancement,
)
from backend.tasks_io.datafeeds.regional_advancement_api import RegionalAdvancementApi


class DatafeedRegionalAdvancement:

    def __init__(self, year: Year) -> None:
        self.api = RegionalAdvancementApi(year)

    @typed_tasklet
    def cmp_advancement(
        self,
    ) -> Generator[Any, Any, Optional[TParsedRegionalAdvancement]]:
        response = yield self.api.cmp_advancement()
        return self._parse(response, RegionalAdvancementParser())

    def _parse(
        self, response: URLFetchResult, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            with Span(f"ra_api_parser:{type(parser).__name__}"):
                return parser.parse(response.json())

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None

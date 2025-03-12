import logging
from typing import Any, cast, Dict, Generator, Optional

from backend.common.models.keys import EventKey, TeamKey
from backend.common.profiler import Span
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.nexus_api import NexusAPI
from backend.tasks_io.datafeeds.parsers.fms_api.simple_json_parser import (
    FMSAPISimpleJsonParser,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase, TParsedResponse


class DatafeedNexus:
    def __init__(self) -> None:
        self.api = NexusAPI()

    @typed_tasklet
    def get_event_team_pit_locations(
        self, event_key: EventKey
    ) -> Generator[Any, Any, Dict[TeamKey, str]]:
        response = yield self.api.pit_locations(event_key)
        return cast(Dict[TeamKey, str], self._parse(response, FMSAPISimpleJsonParser()))

    def _parse(
        self, response: URLFetchResult, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            with Span(f"nexus_api_parser:{type(parser).__name__}"):
                return parser.parse(response.json())

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None

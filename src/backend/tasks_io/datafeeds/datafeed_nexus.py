import logging
from typing import Any, Dict, Generator, Optional

from backend.common.models.event import Event
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import EventKey, TeamKey
from backend.common.profiler import Span
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.nexus_api import NexusAPI
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)
from backend.tasks_io.datafeeds.parsers.nexus_api.queue_status_parser import (
    NexusAPIQueueStatusParser,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase, TParsedResponse


class DatafeedNexus:
    def __init__(self) -> None:
        self.api = NexusAPI()

    @typed_tasklet
    def get_event_team_pit_locations(
        self, event_key: EventKey
    ) -> Generator[Any, Any, Optional[Dict[TeamKey, EventTeamPitLocation]]]:
        response = yield self.api.pit_locations(event_key)
        return self._parse(response, NexusAPIPitLocationParser())

    @typed_tasklet
    def get_event_queue_status(
        self,
        event: Event,
    ) -> Generator[Any, Any, Optional[EventQueueStatus]]:
        response = yield self.api.queue_status(event.key_name)
        return self._parse(response, NexusAPIQueueStatusParser(event))

    def _parse(
        self, response: URLFetchResult, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            with Span(f"nexus_api_parser:{type(parser).__name__}"):
                return parser.parse(response.json())
        elif response.status_code == 404:
            return None

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None

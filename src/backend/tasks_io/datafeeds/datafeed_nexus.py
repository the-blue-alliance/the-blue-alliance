import abc
from typing import Dict, Optional

from backend.common.models.event import Event
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import EventKey, TeamKey
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase, TReturn
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)
from backend.tasks_io.datafeeds.parsers.nexus_api.queue_status_parser import (
    NexusAPIQueueStatusParser,
)


class _DatafeedNexus(DatafeedBase[TReturn]):

    def __init__(self, auth_token: Optional[str] = None, version: str = "v1") -> None:
        super().__init__()
        self.version = version
        self.auth_token = auth_token or NexusApiSecrets.auth_token()

        if not self.auth_token:
            raise Exception(
                f"Missing Nexus API key. Setup {NexusApiSecrets.key()} sitevar"
            )

    def headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
            "Nexus-Api-Key": self.auth_token,
        }

    def url(self) -> str:
        versioned_endpoint = f"{self.version}/{self.endpoint().lstrip('/')}"
        return f"https://frc.nexus/api/{versioned_endpoint}"

    @abc.abstractmethod
    def endpoint(self) -> str: ...


class NexusPitLocations(_DatafeedNexus[Dict[TeamKey, EventTeamPitLocation]]):

    def __init__(self, event_key: EventKey) -> None:
        super().__init__()
        self.event_key = event_key

    def endpoint(self) -> str:
        return f"/event/{self.event_key}/pits"

    def parser(self) -> NexusAPIPitLocationParser:
        return NexusAPIPitLocationParser()


class NexusEventQueueStatus(_DatafeedNexus[Optional[EventQueueStatus]]):
    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event

    def endpoint(self) -> str:
        return f"/event/{self.event.key_name}"

    def parser(self) -> NexusAPIQueueStatusParser:
        return NexusAPIQueueStatusParser(self.event)

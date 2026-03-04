import abc
import logging
from typing import Any, Dict, Generator, Optional

from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb
from google.appengine.runtime import apiproxy_errors

from backend.common.models.event import Event
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import TeamKey
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase, TAPIResponse, TReturn
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)
from backend.tasks_io.datafeeds.parsers.nexus_api.queue_status_parser import (
    NexusAPIQueueStatusParser,
)


class _DatafeedNexus(DatafeedBase[TAPIResponse, TReturn]):

    def __init__(self, auth_token: Optional[str] = None, version: str = "v1") -> None:
        super().__init__()
        self.version = version
        self.auth_token = auth_token or NexusApiSecrets.auth_token()

        if not self.auth_token:
            raise Exception(
                f"Missing Nexus API key. Setup {NexusApiSecrets.key()} sitevar"
            )

    @ndb.tasklet
    def _gen(self) -> Generator[Any, Any, Optional[TReturn]]:
        try:
            result = yield super()._gen()
            return result
        except (apiproxy_errors.ApplicationError, urlfetch_errors.Error) as e:
            logging.warning(f"Nexus datafeed fetch failed: {e}")
            return None

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


class NexusPitLocations(_DatafeedNexus[Any, Dict[TeamKey, EventTeamPitLocation]]):

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event

    def endpoint(self) -> str:
        return f"/event/{self.event.year}{self.event.first_api_code}/pits"

    def parser(self) -> NexusAPIPitLocationParser:
        return NexusAPIPitLocationParser()


class NexusEventQueueStatus(_DatafeedNexus[Any, Optional[EventQueueStatus]]):
    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event

    def endpoint(self) -> str:
        return f"/event/{self.event.year}{self.event.first_api_code}"

    def parser(self) -> NexusAPIQueueStatusParser:
        return NexusAPIQueueStatusParser(self.event)

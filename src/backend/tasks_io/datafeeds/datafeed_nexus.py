import abc
import logging
from typing import Any, Dict, Generator, Optional

from flask import has_request_context, request
from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb
from google.appengine.runtime import apiproxy_errors

from backend.common.datafeeds.datafeed_base import DatafeedBase, TAPIResponse, TReturn
from backend.common.memcache_models.event_sync_status_memcache import (
    EventSyncStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.event_queue_status import EventQueueStatus
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import EventKey, TeamKey
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
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
        event_key = self.event_key()
        endpoint = self._request_endpoint()

        try:
            result = yield super()._gen()

            if event_key and endpoint:
                if result is None:
                    EventSyncStatusMemcache(event_key).record_failure(endpoint)
                else:
                    EventSyncStatusMemcache(event_key).record_success(endpoint)

            return result
        except (apiproxy_errors.ApplicationError, urlfetch_errors.Error) as e:
            if event_key and endpoint:
                EventSyncStatusMemcache(event_key).record_failure(endpoint)
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

    def _request_endpoint(self) -> Optional[str]:
        if not has_request_context():
            return None
        return request.endpoint

    def event_key(self) -> Optional[EventKey]:
        return None

    @abc.abstractmethod
    def endpoint(self) -> str: ...


class NexusPitLocations(_DatafeedNexus[Any, Dict[TeamKey, EventTeamPitLocation]]):

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event

    def endpoint(self) -> str:
        return f"/event/{self.event.year}{self.event.first_api_code}/pits"

    def event_key(self) -> Optional[EventKey]:
        return self.event.key_name

    def parser(self) -> NexusAPIPitLocationParser:
        return NexusAPIPitLocationParser()


class NexusEventQueueStatus(_DatafeedNexus[Any, Optional[EventQueueStatus]]):
    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event

    def endpoint(self) -> str:
        return f"/event/{self.event.year}{self.event.first_api_code}"

    def event_key(self) -> Optional[EventKey]:
        return self.event.key_name

    def parser(self) -> NexusAPIQueueStatusParser:
        return NexusAPIQueueStatusParser(self.event)

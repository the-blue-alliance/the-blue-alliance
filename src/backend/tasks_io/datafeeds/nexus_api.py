from typing import Any, Generator, Optional

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture
from backend.common.models.keys import EventKey
from backend.common.profiler import Span
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


class NexusAPI:

    def __init__(self, auth_token: Optional[str] = None) -> None:
        if not auth_token:
            auth_token = NexusApiSecrets.auth_token()

        if not auth_token:
            raise Exception(
                f"Missing Nexus API key. Setup {NexusApiSecrets.key()} sitevar"
            )

        self.auth_token = auth_token
        self.ndb_context = ndb.get_context()

    def pit_locations(self, event_key: EventKey) -> TypedFuture[URLFetchResult]:
        endpoint = f"/event/{event_key}/pits"
        return self._get(endpoint)

    @typed_tasklet
    def _get(
        self, endpoint: str, version: str = "v1"
    ) -> Generator[Any, Any, URLFetchResult]:
        # Remove any leading / - we'll add it later (safer then adding a slash)
        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"

        url = f"https://frc.nexus/api/{versioned_endpoint}"
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
            "Nexus-Api-Key": self.auth_token,
        }

        with Span(f"nexus_api_fetch:{endpoint}"):
            resp = yield self.ndb_context.urlfetch(url, headers=headers, deadline=30)
            return URLFetchResult(url, resp)

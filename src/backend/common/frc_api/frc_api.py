import datetime
import logging
import os
import re
from typing import Any, Generator, Literal, Optional

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture
from backend.common.models.keys import Year
from backend.common.profiler import Span
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


TCompLevel = Literal["qual", "playoff"]


class FRCAPI:
    STORAGE_BUCKET_PATH = "tbatv-prod-hrd.appspot.com"
    STORAGE_BUCKET_BASE_DIR = "frc-api-response"

    class ValidationError(Exception):
        pass

    @classmethod
    def with_credentials(cls, username: str, authkey: str):
        auth_token = FMSApiSecrets.generate_auth_token(username, authkey)
        return cls(auth_token)

    def __init__(
        self,
        auth_token: Optional[str] = None,
        sim_time: Optional[datetime.datetime] = None,
        sim_api_version: Optional[str] = None,
    ):
        # Load auth_token from Sitevar if not specified
        if not auth_token:
            auth_token = FMSApiSecrets.auth_token()

        if not auth_token:
            raise Exception(
                f"Missing FRC API auth token. Setup {FMSApiSecrets.key()} sitevar."
            )

        self.ndb_context = ndb.get_context()
        self.auth_token = auth_token
        self._sim_time = sim_time
        self._sim_api_version = sim_api_version

    def root(self) -> TypedFuture[URLFetchResult]:
        return self._get("/")

    def team_details(self, year: Year, team_number: int) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/teams?teamNumber={team_number}"
        return self._get(endpoint)

    def team_avatar(self, year: Year, team_number: int) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/avatars?teamNumber={team_number}"
        return self._get(endpoint)

    def event_list(self, year: Year) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/events"
        return self._get(endpoint)

    def event_info(self, year: Year, event_short: str) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/events?eventCode={event_short}"
        return self._get(endpoint)

    def event_teams(
        self, year: Year, event_short: str, page: int
    ) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/teams?eventCode={event_short}&page={page}"
        return self._get(endpoint)

    def event_team_avatars(
        self, year: Year, event_short: str, page: int
    ) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/avatars?eventCode={event_short}&page={page}"
        return self._get(endpoint)

    def alliances(self, year: Year, event_short: str) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/alliances/{event_short}"
        return self._get(endpoint)

    def rankings(self, year: Year, event_short: str) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/rankings/{event_short}"
        return self._get(endpoint)

    def match_schedule(
        self, year: Year, event_short: str, level: TCompLevel
    ) -> TypedFuture[URLFetchResult]:
        # This does not include results
        endpoint = f"/{year}/schedule/{event_short}?tournamentLevel={level}"
        return self._get(endpoint)

    def matches(
        self, year: Year, event_short: str, level: TCompLevel
    ) -> TypedFuture[URLFetchResult]:
        # This includes both played/unplayed matches at the event
        # but doesn't include full results
        endpoint = f"/{year}/matches/{event_short}?tournamentLevel={level}"
        return self._get(endpoint)

    def match_scores(
        self, year: Year, event_short: str, level: TCompLevel
    ) -> TypedFuture[URLFetchResult]:
        # technically "qual"/"playoff" are invalid tournament levels as per the docs,
        # but they seem to work?
        endpoint = f"/{year}/scores/{event_short}/{level}"
        return self._get(endpoint)

    def awards(
        self,
        year: Year,
        event_code: Optional[str] = None,
        team_number: Optional[int] = None,
    ) -> TypedFuture[URLFetchResult]:
        if not event_code and not team_number:
            raise FRCAPI.ValidationError(
                "awards expects either an event_code, team_number, or both"
            )

        if event_code is not None and team_number is not None:
            endpoint = f"/{year}/awards/eventteam/{event_code}/{team_number}"
        elif event_code is not None:
            endpoint = f"/{year}/awards/event/{event_code}"
        else:  # team_number is not None
            endpoint = f"/{year}/awards/team/{team_number}"

        return self._get(endpoint)

    def district_list(self, year: Year) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/districts"
        return self._get(endpoint)

    def district_rankings(
        self, year: Year, district_short: str, page: int
    ) -> TypedFuture[URLFetchResult]:
        endpoint = (
            f"/{year}/rankings/district?districtCode={district_short}&page={page}"
        )
        return self._get(endpoint)

    """ Attempt to fetch the endpoint from the FRC API

        Returns:
            The Flask response object - should be used by the consumer.
    """

    @typed_tasklet
    def _get(
        self, endpoint: str, version: str = "v3.0"
    ) -> Generator[Any, Any, URLFetchResult]:
        # Remove any leading / - we'll add it later (safer then adding a slash)
        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"
        if self._sim_time is not None:
            return self._get_simulated(endpoint, self._sim_api_version or version)

        url = f"https://frc-api.firstinspires.org/{versioned_endpoint}"
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
            "Authorization": f"Basic {self.auth_token}",
        }

        with Span(f"frc_api_fetch:{endpoint}"):
            resp = yield self.ndb_context.urlfetch(url, headers=headers, deadline=30)
            return URLFetchResult(url, resp)

    @staticmethod
    def get_cached_gcs_files(gcs_dir_name: str):
        """
        Get the locally cached files or from GCS if not cached.
        If getting from GCS, cache the files locally.
        To avoid issues with Windows, `:` are replaced with `_` and `?` are replaced with `@` in the filenames.
        """
        safe_dir_name = gcs_dir_name.replace(":", "_").replace("?", "@")
        path = os.path.join(
            os.path.dirname(__file__), f"gcs_test_data_cache/{safe_dir_name}"
        )
        if os.path.exists(path):
            files = [f"{safe_dir_name}{p}" for p in os.listdir(path)]
        else:
            from backend.common.storage import get_files, read

            gcs_files = get_files(gcs_dir_name)
            files = []
            for gcs_file in gcs_files:
                safe_file_name = (
                    gcs_file.split("/")[-1].replace(":", "_").replace("?", "@")
                )
                filename = os.path.join(path, safe_file_name)
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                content = read(gcs_file)
                if content is not None:
                    with open(filename, "w") as f:
                        f.write(content)
                    files.append(f"{safe_dir_name}/{safe_file_name}")
        return sorted(files)

    def _get_simulated(self, endpoint: str, version: str) -> URLFetchResult:
        if version == "v2.0" and "/schedule" in endpoint and "hybrid" not in endpoint:
            # The hybrid schedule endpoint doesn't exist in newer versions,
            # so hack the URLs to make things work with older data
            # /2022/schedule/CADA/qual/hybrid
            # /2022/schedule/CADA?tournamentLevel=qual
            regex = re.search(r"/(\d+)/schedule/(\w+)\?tournamentLevel=(\w+)", endpoint)
            if regex:
                endpoint = f"/{regex.group(1)}/schedule/{regex.group(2)}/{regex.group(3)}/hybrid"

        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"
        url = f"https://frc-api.firstinspires.org/{versioned_endpoint}"

        # Get list of responses
        try:
            gcs_dir_name = (
                f"{self.STORAGE_BUCKET_BASE_DIR}/{version}/{endpoint.lstrip('/')}/"
            )
            gcs_files = self.get_cached_gcs_files(gcs_dir_name)

            # Find appropriate timed response
            last_file_name = None
            for filename in gcs_files:
                time_str = filename.split("/")[-1].replace(".json", "").strip()
                file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H_%M_%S.%f")
                if file_time <= self._sim_time:
                    last_file_name = filename
                else:
                    break

            # Fetch response
            content: Optional[str] = None
            if last_file_name:
                with open(
                    os.path.join(
                        os.path.dirname(__file__),
                        f"gcs_test_data_cache/{last_file_name}",
                    ),
                    "r",
                ) as f:
                    content = f.read()

            if content is None:
                return URLFetchResult.mock_for_content(url, 200, "{}")

            return URLFetchResult.mock_for_content(url, 200, content)
        except Exception:
            logging.exception("Error fetching sim frc api")
            return URLFetchResult.mock_for_content(url, 500, "")

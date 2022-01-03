import datetime
import json
import logging
from typing import Literal, Optional

import requests

from backend.common.models.keys import Year
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets


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

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Basic {auth_token}"})
        self._sim_time = sim_time
        self._sim_api_version = sim_api_version

    def root(self) -> requests.Response:
        return self._get("/")

    def team_details(self, year: Year, team_number: int) -> requests.Response:
        endpoint = f"/{year}/teams?teamNumber={team_number}"
        return self._get(endpoint)

    def team_avatar(self, year: Year, team_number: int) -> requests.Response:
        endpoint = f"/{year}/avatars?teamNumber={team_number}"
        return self._get(endpoint)

    def event_list(self, year: Year) -> requests.Response:
        endpoint = f"/{year}/events"
        return self._get(endpoint)

    def event_info(self, year: Year, event_short: str) -> requests.Response:
        endpoint = f"/{year}/events?eventCode={event_short}"
        return self._get(endpoint)

    def event_teams(self, year: Year, event_short: str, page: int) -> requests.Response:
        endpoint = f"/{year}/teams?eventCode={event_short}&page={page}"
        return self._get(endpoint)

    def event_team_avatars(
        self, year: Year, event_short: str, page: int
    ) -> requests.Response:
        endpoint = f"/{year}/avatars?eventCode={event_short}&page={page}"
        return self._get(endpoint)

    def alliances(self, year: Year, event_short: str) -> requests.Response:
        endpoint = f"/{year}/alliances/{event_short}"
        return self._get(endpoint)

    def rankings(self, year: Year, event_short: str) -> requests.Response:
        endpoint = f"/{year}/rankings/{event_short}"
        return self._get(endpoint)

    def matches_hybrid(
        self, year: Year, event_short: str, level: Literal["qual", "playoff"]
    ) -> requests.Response:
        endpoint = f"/{year}/schedule/{event_short}/{level}/hybrid"

        # hybrid schedule requires v2.0 because it doesn't exist in v3.0
        # https://usfirst.collab.net/sf/go/artf6030
        return self._get(endpoint, version="v2.0")

    def match_scores(
        self, year: Year, event_short: str, level: Literal["qual", "playoff"]
    ) -> requests.Response:
        # technically "qual"/"playoff" are invalid tournament levels as per the docs,
        # but they seem to work?
        endpoint = f"/{year}/scores/{event_short}/{level}"
        return self._get(endpoint)

    def awards(
        self,
        year: Year,
        event_code: Optional[str] = None,
        team_number: Optional[int] = None,
    ) -> requests.Response:
        if not event_code and not team_number:
            raise FRCAPI.ValidationError(
                "awards expects either an event_code, team_number, or both"
            )

        # Work around a bug with the v3.0 awards endpoint where teamNumber is non-optional.
        # Passing a `0` will get us all awards for an Event
        # https://usfirst.collab.net/sf/go/artf6025
        if event_code is not None and team_number is None:
            team_number = 0

        if event_code is not None and team_number is not None:
            endpoint = f"/{year}/awards/{event_code}/{team_number}"
        else:
            endpoint = f"/{year}/awards/{event_code or team_number}"

        return self._get(endpoint)

    def district_list(self, year: Year) -> requests.Response:
        endpoint = f"/{year}/districts"
        return self._get(endpoint)

    def district_rankings(
        self, year: Year, district_short: str, page: int
    ) -> requests.Response:
        endpoint = (
            f"/{year}/rankings/district?districtCode={district_short}&page={page}"
        )
        return self._get(endpoint)

    """ Attempt to fetch the endpoint from the FRC API

        Returns:
            The Flask response object - should be used by the consumer.
    """

    def _get(self, endpoint: str, version: str = "v3.0") -> requests.Response:
        # Remove any leading / - we'll add it later (safer then adding a slash)
        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"
        if self._sim_time is not None:
            return self._get_simulated(endpoint, self._sim_api_version or version)

        url = f"https://frc-api.firstinspires.org/{versioned_endpoint}"
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
        }

        return self.session.get(url, headers=headers)

    def _get_simulated(self, endpoint: str, version: str) -> requests.Response:
        from unittest.mock import Mock
        from backend.common.storage import (
            get_files as cloud_storage_get_files,
            read as cloud_storage_read,
        )

        # Get list of responses
        try:
            gcs_dir_name = (
                f"{self.STORAGE_BUCKET_BASE_DIR}/{version}/{endpoint.lstrip('/')}/"
            )
            gcs_files = cloud_storage_get_files(gcs_dir_name)

            # Find appropriate timed response
            last_file_name = None
            for filename in gcs_files:
                time_str = (
                    filename.replace(gcs_dir_name, "").replace(".json", "").strip()
                )
                file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                if file_time <= self._sim_time:
                    last_file_name = filename
                else:
                    break

            # Fetch response
            content: Optional[str] = None
            if last_file_name:
                content = cloud_storage_read(last_file_name)

            if content is None:
                empty_response = Mock(spec=requests.Response)
                empty_response.status_code = 200
                empty_response.json.return_value = {}
                empty_response.url = ""
                return empty_response

            full_response = Mock(spec=requests.Response)
            full_response.status_code = 200
            full_response.json.return_value = json.loads(content)
            full_response.url = ""
            return full_response
        except Exception:
            logging.exception("Error fetching sim frc api")
            error_response = Mock(spec=requests.Response)
            error_response.status_code = 500
            error_response.url = ""
            return error_response

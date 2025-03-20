import datetime
import json
import logging
import os
import re
from typing import Any, cast, Dict, Generator, Literal, Optional

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.environment import Environment
from backend.common.futures import TypedFuture
from backend.common.models.keys import Year
from backend.common.profiler import Span
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


TCompLevel = Literal["qual", "playoff"]


class FRCAPI:
    BASE_URL = "https://frc-api.firstinspires.org"
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
        save_response: bool = False,
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
        self._save_response = save_response

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

    def hybrid_schedule(
        self, year: Year, event_short: str, level: TCompLevel
    ) -> TypedFuture[URLFetchResult]:
        endpoint = f"/{year}/schedule/{event_short}/{level}/hybrid"
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

        url = f"{self.BASE_URL}/{versioned_endpoint}"
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
            "Authorization": f"Basic {self.auth_token}",
        }

        with Span(f"frc_api_fetch:{endpoint}"):
            r = yield self.ndb_context.urlfetch(url, headers=headers, deadline=30)
            response = URLFetchResult(url, r)
            if response.status_code == 200:
                with Span(f"maybe_save_fmsapi_response:{response.url}"):
                    self._maybe_save_response(response.url, response.content)

            return response

    def _maybe_save_response(self, url: str, content: str) -> None:
        if not Environment.save_frc_api_response() or not self._save_response:
            return

        endpoint = url.replace(f"{self.BASE_URL}/", "")
        gcs_dir_name = f"{FRCAPI.STORAGE_BUCKET_BASE_DIR}/{endpoint}/"

        from backend.common.storage import (
            get_files as cloud_storage_get_files,
            read as cloud_storage_read,
            write as cloud_storage_write,
        )

        # Check to see if the last saved response is the same as the current response
        try:
            # Check for last response
            gcs_files = cloud_storage_get_files(gcs_dir_name)
            last_item_filename = gcs_files[-1] if len(gcs_files) > 0 else None

            write_new = True
            if last_item_filename is not None:
                last_json_file = cloud_storage_read(last_item_filename)
                if last_json_file == content:
                    write_new = False  # Do not write if content didn't change

            if write_new:
                file_name = gcs_dir_name + "{}.json".format(datetime.datetime.now())
                cloud_storage_write(file_name, content)
        except Exception:
            logging.exception("Error saving API response for: {}".format(url))

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
        sim_year = none_throws(self._sim_time).year
        if version == "v2.0" and "/schedule" in endpoint and "hybrid" not in endpoint:
            # The hybrid schedule endpoint doesn't exist in newer versions,
            # so hack the URLs to make things work with older data
            # /2022/schedule/CADA/qual/hybrid
            # /2022/schedule/CADA?tournamentLevel=qual
            regex = re.search(r"/(\d+)/schedule/(\w+)\?tournamentLevel=(\w+)", endpoint)
            if regex:
                endpoint = f"/{regex.group(1)}/schedule/{regex.group(2)}/{regex.group(3)}/hybrid"
        elif (
            version == "v3.0"
            and "/schedule" in endpoint
            and "hybrid" in endpoint
            and sim_year < 2025
        ):
            # The hybrid schedule endpoint didn't exist in v3 until the 2025 season, so merge scores/schedule
            return self._simulate_v3_hybrid_schedule(endpoint, version)

        return self._get_api_response_from_gcs(endpoint, version)

    def _simulate_v3_hybrid_schedule(
        self, endpoint: str, version: str
    ) -> URLFetchResult:
        url_parts = endpoint.split("/")
        year = int(url_parts[1])
        event_code = url_parts[3]
        comp_level = url_parts[4]

        schedule_result = self._get_api_response_from_gcs(
            f"/{year}/schedule/{event_code}?tournamentLevel={comp_level}", version
        )
        matches_result = self._get_api_response_from_gcs(
            f"/{year}/matches/{event_code}?tournamentLevel={comp_level}", version
        )
        merged_content = self._merge_match_schedule_and_results(
            cast(Dict, schedule_result.json()), cast(Dict, matches_result.json())
        )

        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"
        hybrid_url = f"{self.BASE_URL}/{versioned_endpoint}"
        return URLFetchResult.mock_for_content(
            hybrid_url, 200, json.dumps(merged_content)
        )

    def _get_api_response_from_gcs(self, endpoint: str, version: str) -> URLFetchResult:
        versioned_endpoint = f"{version}/{endpoint.lstrip('/')}"
        url = f"{self.BASE_URL}/{versioned_endpoint}"
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

    def _merge_match_schedule_and_results(self, schedule: Dict, matches: Dict) -> Dict:
        scheduled_matches = schedule["Schedule"]
        if "Matches" not in matches:
            matches["Matches"] = [{}] * len(scheduled_matches)
        return {
            "Schedule": [
                self._merge_match(s, m)
                for s, m in zip(scheduled_matches, matches["Matches"])
            ]
        }

    @classmethod
    def _merge_match(cls, scheduled: Dict, result: Dict) -> Dict:
        # Over the years, both "Teams" and "teams" have been used in FRC API responses...
        teams_key = "Teams" if "Teams" in scheduled else "teams"

        # 2024, Week 4: As part of attempting to restore sync,
        # schedules sync with teams [1, 2, 3] in to-be-played playoff matches
        # In a case where the only teams for a match are those three, overwrite
        # the team numbers in each station to None
        schedule_team_numbers = [t["teamNumber"] for t in scheduled.get(teams_key)]
        if set(schedule_team_numbers) == {1, 2, 3}:
            scheduled["teams"] = [
                {**t, "teamNumber": None} for t in scheduled.get(teams_key)
            ]

        for field, value in result.items():
            if field == teams_key:
                for team in value:
                    schedule_idx, schedule_team = next(
                        filter(
                            lambda t: t[1]["teamNumber"] == team["teamNumber"],
                            enumerate(scheduled["teams"]),
                        ),
                        (None, None),
                    )
                    if schedule_team is None:
                        # 2024, Week 3: Upstream FMS sync issues leading to schedules returned with no teams
                        # Some match results have been sync'd, so patch around this where we can
                        scheduled["teams"].append(team)
                    else:
                        scheduled["teams"][schedule_idx].update(team)
            else:
                scheduled[field] = value
        return scheduled

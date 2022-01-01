import datetime
import logging
from typing import List, Optional, Set, Tuple

import requests
from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.environment import Environment
from backend.common.frc_api import FRCAPI
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, Year
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_awards_parser import (
    FMSAPIAwardsParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_list_parser import (
    FMSAPIDistrictListParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_list_parser import (
    FMSAPIEventListParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_root_parser import (
    FMSAPIRootParser,
    RootInfo,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_avatar_parser import (
    FMSAPITeamAvatarParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_details_parser import (
    FMSAPITeamDetailsParser,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase, TParsedResponse

# from parsers.fms_api.fms_api_district_rankings_parser import FMSAPIDistrictRankingsParser
# from parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
# from parsers.fms_api.fms_api_event_rankings_parser import FMSAPIEventRankingsParser, FMSAPIEventRankings2Parser
# from parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser, FMSAPIMatchDetailsParser


class DatafeedFMSAPI:

    EVENT_SHORT_EXCEPTIONS = {
        "arc": "archimedes",
        "cars": "carson",
        "carv": "carver",
        "cur": "curie",
        "dal": "daly",
        "dar": "darwin",
        "gal": "galileo",
        "hop": "hopper",
        "new": "newton",
        "roe": "roebling",
        "tes": "tesla",
        "tur": "turing",
    }

    SUBDIV_TO_DIV = {  # 2015, 2016
        "arc": "arte",
        "cars": "gaca",
        "carv": "cuca",
        "cur": "cuca",
        "gal": "gaca",
        "hop": "neho",
        "new": "neho",
        "tes": "arte",
    }

    SUBDIV_TO_DIV_2017 = {  # 2017+
        "arc": "arda",
        "cars": "cate",
        "carv": "cane",
        "cur": "cuda",
        "dal": "arda",
        "dar": "cuda",
        "gal": "garo",
        "hop": "hotu",
        "new": "cane",
        "roe": "garo",
        "tes": "cate",
        "tur": "hotu",
    }

    def __init__(self) -> None:
        self.api = FRCAPI()

    def get_root_info(self) -> Optional[RootInfo]:
        root_response = self.api.root()
        return self._parse(root_response, FMSAPIRootParser())

    # Returns a tuple: (list(Event), list(District))
    def get_event_list(self, year: Year) -> Tuple[List[Event], List[District]]:
        event_list_response = self.api.event_list(year)
        result = self._parse(event_list_response, FMSAPIEventListParser(year))
        return result or ([], [])

    # Returns a tuple: (list(Event), list(District))
    def get_event_details(
        self, event_key: EventKey
    ) -> Tuple[List[Event], List[District]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        api_event_short = self._get_event_short(event_short, event)
        event_info_response = self.api.event_info(year, api_event_short)
        result = self._parse(
            event_info_response, FMSAPIEventListParser(year, short=event_short)
        )
        return result or ([], [])

    # Returns list of tuples (team, districtteam, robot)
    def get_event_teams(
        self, event_key: EventKey
    ) -> List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]:
        year = int(event_key[:4])
        event_code = self._get_event_short(event_key[4:])

        parser = FMSAPITeamDetailsParser(year)
        models: List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]] = []

        more_pages = True
        page = 1

        while more_pages:
            page_response = self.api.event_teams(year, event_code, page)
            result = self._parse(page_response, parser)
            if result is None:
                break

            partial_models, more_pages = result
            models.extend(partial_models or [])

            page = page + 1

        return models

    def get_awards(self, event: Event) -> List[Award]:
        awards = []

        # 8 subdivisions from 2015+ have awards listed under 4 divisions
        if event.event_type_enum == EventType.CMP_DIVISION and event.year >= 2015:
            event_team_keys = EventTeam.query(EventTeam.event == event.key).fetch(
                keys_only=True
            )
            valid_team_nums = {
                int(etk.id().split("_")[1][3:]) for etk in event_team_keys
            }

            if event.year >= 2017:
                division = self.SUBDIV_TO_DIV_2017[event.event_short]
            else:
                division = self.SUBDIV_TO_DIV[event.event_short]

            api_awards_response = self.api.awards(
                event.year, event_code=DatafeedFMSAPI._get_event_short(division)
            )
            awards += (
                self._parse(
                    api_awards_response, FMSAPIAwardsParser(event, valid_team_nums)
                )
                or []
            )

        api_awards_response = self.api.awards(
            event.year,
            event_code=DatafeedFMSAPI._get_event_short(event.event_short, event),
        )
        awards += self._parse(api_awards_response, FMSAPIAwardsParser(event)) or []

        return awards

    def get_event_team_avatars(
        self, event_key: EventKey
    ) -> Tuple[List[Media], Set[ndb.Key]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        parser = FMSAPITeamAvatarParser(year)
        api_event_short = DatafeedFMSAPI._get_event_short(event_short, event)
        avatars: List[Media] = []
        keys_to_delete: Set[ndb.Key] = set()

        more_pages = True
        page = 1

        while more_pages:
            avatar_result = self.api.event_team_avatars(year, api_event_short, page)
            result = self._parse(avatar_result, parser)
            if result is None:
                break

            parser_result, more_pages = result
            (partial_avatars, partial_keys_to_delete) = parser_result or ([], {})
            avatars.extend(partial_avatars)
            keys_to_delete = keys_to_delete.union(partial_keys_to_delete)

            page = page + 1

        return avatars, keys_to_delete

    # Returns a list of districts
    def get_district_list(self, year: Year) -> List[District]:
        district_list_response = self.api.district_list(year)
        result = self._parse(district_list_response, FMSAPIDistrictListParser(year))
        return result or []

    @classmethod
    def _get_event_short(self, event_short: str, event: Optional[Event] = None) -> str:
        # First, check if we've manually set the FRC API key
        if event and event.first_code:
            return event.first_code

        # Otherwise, check hard-coded exceptions
        return DatafeedFMSAPI.EVENT_SHORT_EXCEPTIONS.get(event_short, event_short)

    def _parse(
        self, response: requests.Response, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            ApiStatusFMSApiDown.set_down(False)
            self._maybe_save_response(response.url, response.content.decode())
            return parser.parse(response.json())
        elif response.status_code // 100 == 5:
            # 5XX error - something is wrong with the server
            ApiStatusFMSApiDown.set_down(True)

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None

    def _maybe_save_response(self, url: str, content: str) -> None:
        if not Environment.save_frc_api_response():
            return

        endpoint = url.replace("https://frc-api.firstinspires.org/", "")
        gcs_dir_name = f"/tbatv-prod-hrd.appspot.com/frc-api-response/{endpoint}/"

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

    """
    def getEventAlliances(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        alliances = self._parse(self.FMS_API_EVENT_ALLIANCES_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)), FMSAPIEventAlliancesParser())
        return alliances

    def getMatches(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        hs_parser = FMSAPIHybridScheduleParser(year, event_short)
        detail_parser = FMSAPIMatchDetailsParser(year, event_short)
        qual_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)), hs_parser)
        playoff_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)), hs_parser)
        qual_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_QUAL_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)), detail_parser)
        playoff_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_PLAYOFF_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)), detail_parser)

        # Organize matches by key
        matches_by_key = {}
        qual_matches = qual_matches_future.get_result()
        if qual_matches is not None:
            for match in qual_matches[0]:
                matches_by_key[match.key.id()] = match
        playoff_matches = playoff_matches_future.get_result()
        remapped_playoff_matches = {}
        if playoff_matches is not None:
            for match in playoff_matches[0]:
                matches_by_key[match.key.id()] = match
            remapped_playoff_matches = playoff_matches[1]

        # Add details to matches based on key
        qual_details = qual_details_future.get_result()
        qual_details_items = qual_details.items() if qual_details is not None else []
        playoff_details = playoff_details_future.get_result()
        playoff_details_items = playoff_details.items() if playoff_details is not None else []
        for match_key, match_details in qual_details_items + playoff_details_items:
            # Deal with remapped playoff matches, defaulting to the original match key
            match_key = remapped_playoff_matches.get(match_key, match_key)
            if match_key in matches_by_key:
                matches_by_key[match_key].score_breakdown_json = json.dumps(match_details)

        return filter(
            lambda m: not FMSAPIHybridScheduleParser.is_blank_match(m),
            matches_by_key.values())

    def getEventRankings(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        result = self._parse(
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN % (year, DatafeedFMSAPI._get_event_short(event_short, event)),
            [FMSAPIEventRankingsParser(year), FMSAPIEventRankings2Parser(year)])
        if result:
            return result
        else:
            return None, None

    def getTeamDetails(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        result = self._parse(self.FMS_API_TEAM_DETAILS_URL_PATTERN % (year, team_number), FMSAPITeamDetailsParser(year))
        if result:
            return result[0]
        else:
            return None

    def getTeamAvatar(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        avatars, keys_to_delete, _ = self._parse(self.FMS_API_TEAM_AVATAR_URL_PATTERN % (year, team_number), FMSAPITeamAvatarParser(year))
        if avatars:
            return avatars[0], keys_to_delete
        else:
            return None, keys_to_delete

    def getDistrictRankings(self, district_key):
        district = District.get_by_id(district_key)
        if not district:
            return None

        year = int(district_key[:4])
        district_short = district_key[4:]
        advancement = {}

        more_pages = True
        page = 1

        while more_pages:
            url = self.FMS_API_DISTRICT_RANKINGS_PATTERN % (year, district_short.upper(), page)
            # NOTE: THIS API CHANGED and does no longer take an `advandement` dict. Do this updating in this method.
            result = self._parse(url, FMSAPIDistrictRankingsParser(advancement))
            if not result:
                break

            advancement, more_pages = result

            page = page + 1

        district.advancement = advancement
        return [district]
    """

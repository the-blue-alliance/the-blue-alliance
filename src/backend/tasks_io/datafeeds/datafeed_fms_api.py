import datetime
import json
import logging
from typing import Any, Generator, List, Optional, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.frc_api import FRCAPI
from backend.common.models.alliance import EventAlliance
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_advancement import DistrictAdvancement
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.profiler import Span
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_awards_parser import (
    FMSAPIAwardsParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_list_parser import (
    FMSAPIDistrictListParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_rankings_parser import (
    FMSAPIDistrictRankingsParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_alliances_parser import (
    FMSAPIEventAlliancesParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_list_parser import (
    FMSAPIEventListParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_rankings_parser import (
    FMSAPIEventRankingsParser,
)
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIHybridScheduleParser,
    FMSAPIMatchDetailsParser,
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


class DatafeedFMSAPI:
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

    def __init__(
        self,
        sim_time: Optional[datetime.datetime] = None,
        sim_api_version: Optional[str] = None,
        save_response: bool = False,
    ) -> None:
        self.api = FRCAPI(
            sim_time=sim_time,
            sim_api_version=sim_api_version,
            save_response=save_response,
        )

    @typed_tasklet
    def get_root_info(self) -> Generator[Any, Any, Optional[RootInfo]]:
        root_response = yield self.api.root()
        return self._parse(root_response, FMSAPIRootParser())

    @typed_tasklet
    def get_team_details(
        self, year: Year, team_key: TeamKey
    ) -> Generator[
        Any, Any, Optional[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]
    ]:
        team_number = int(team_key[3:])  # everything after 'frc'
        api_response = yield self.api.team_details(year, team_number)
        result = self._parse(api_response, FMSAPITeamDetailsParser(year))
        if result:
            models, _ = result
            return next(iter(models), None) if models else None
        else:
            return None

    @typed_tasklet
    def get_team_avatar(
        self, year: Year, team_key: TeamKey
    ) -> Generator[Any, Any, Tuple[List[Media], Set[ndb.Key]]]:
        team_number = int(team_key[3:])  # everything after 'frc'
        api_response = yield self.api.team_avatar(year, team_number)
        result = self._parse(api_response, FMSAPITeamAvatarParser(year))
        if result:
            (avatar_result, _) = result
            if avatar_result:
                return avatar_result
        return [], set()

    # Returns a tuple: (list(Event), list(District))
    @typed_tasklet
    def get_event_list(
        self, year: Year
    ) -> Generator[Any, Any, Tuple[List[Event], List[District]]]:
        event_list_response = yield self.api.event_list(year)
        result = self._parse(event_list_response, FMSAPIEventListParser(year))
        return result or ([], [])

    # Returns a tuple: (list(Event), list(District))
    @typed_tasklet
    def get_event_details(
        self, event_key: EventKey
    ) -> Generator[Any, Any, Tuple[List[Event], List[District]]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        api_event_short = self._get_event_short(year, event_short, event)
        event_info_response = yield self.api.event_info(year, api_event_short)
        result = self._parse(
            event_info_response,
            FMSAPIEventListParser(year, short=event_short),
        )
        return result or ([], [])

    # Returns list of tuples (team, districtteam, robot)
    @typed_tasklet
    def get_event_teams(
        self, event_key: EventKey
    ) -> Generator[
        Any, Any, List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]
    ]:
        year = int(event_key[:4])
        event_short = event_key[4:]
        event = Event.get_by_id(event_key)
        event_code = self._get_event_short(year, event_short, event)

        parser = FMSAPITeamDetailsParser(year)
        models: List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]] = []

        more_pages = True
        page = 1

        while more_pages:
            page_response = yield self.api.event_teams(year, event_code, page)
            result = self._parse(page_response, parser)
            if result is None:
                break

            partial_models, more_pages = result
            models.extend(partial_models or [])

            page = page + 1

        return models

    @typed_tasklet
    def get_awards(self, event: Event) -> Generator[Any, Any, List[Award]]:
        awards = []

        # 8 subdivisions from 2015-2021 have awards listed under 4 divisions
        if (
            event.event_type_enum == EventType.CMP_DIVISION
            and event.year >= 2015
            and event.year < 2022
        ):
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

            api_awards_response = yield self.api.awards(event.year, event_code=division)
            awards += (
                self._parse(
                    api_awards_response,
                    FMSAPIAwardsParser(event, valid_team_nums),
                )
                or []
            )

        api_awards_response = yield self.api.awards(
            event.year,
            event_code=DatafeedFMSAPI._get_event_short(
                event.year, event.event_short, event
            ),
        )
        awards += self._parse(api_awards_response, FMSAPIAwardsParser(event)) or []

        return awards

    @typed_tasklet
    def get_event_alliances(
        self, event_key: EventKey
    ) -> Generator[Any, Any, List[EventAlliance]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        api_event_short = self._get_event_short(year, event_short, event)
        api_response = yield self.api.alliances(year, api_event_short)
        alliances = self._parse(api_response, FMSAPIEventAlliancesParser())
        return alliances or []

    @typed_tasklet
    def get_event_rankings(
        self, event_key: EventKey
    ) -> Generator[Any, Any, List[EventRanking]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        api_event_short = self._get_event_short(year, event_short, event)
        api_response = yield self.api.rankings(year, api_event_short)
        result = self._parse(api_response, FMSAPIEventRankingsParser(year))
        return result or []

    @typed_tasklet
    def get_event_matches(
        self, event_key: EventKey
    ) -> Generator[Any, Any, List[Match]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        hs_parser = FMSAPIHybridScheduleParser(year, event_short)
        detail_parser = FMSAPIMatchDetailsParser(year, event_short)

        api_event_short = DatafeedFMSAPI._get_event_short(year, event_short, event)

        (
            qual_hybrid_schedule_result,
            playoff_hybrid_schedule_result,
            qual_scores_result,
            playoff_scores_result,
        ) = yield (
            self.api.hybrid_schedule(year, api_event_short, "qual"),
            self.api.hybrid_schedule(year, api_event_short, "playoff"),
            self.api.match_scores(year, api_event_short, "qual"),
            self.api.match_scores(year, api_event_short, "playoff"),
        )

        qual_matches_merged = self._parse(qual_hybrid_schedule_result, hs_parser)
        playoff_matches_merged = self._parse(playoff_hybrid_schedule_result, hs_parser)

        # Organize matches by key
        matches_by_key = {}
        if qual_matches_merged:
            for match in qual_matches_merged[0]:
                matches_by_key[match.key.id()] = match

        remapped_playoff_matches = {}
        if playoff_matches_merged:
            for match in playoff_matches_merged[0]:
                matches_by_key[match.key.id()] = match
            remapped_playoff_matches = playoff_matches_merged[1]

        # Add details to matches based on key
        qual_details = self._parse(qual_scores_result, detail_parser) or {}
        playoff_details = self._parse(playoff_scores_result, detail_parser) or {}
        for match_key, match_details in {**qual_details, **playoff_details}.items():
            # Deal with remapped playoff matches, defaulting to the original match key
            match_key = remapped_playoff_matches.get(match_key, match_key)
            if match_key in matches_by_key:
                matches_by_key[match_key].score_breakdown_json = json.dumps(
                    match_details
                )

        return list(
            filter(
                lambda m: not FMSAPIHybridScheduleParser.is_blank_match(m),
                matches_by_key.values(),
            )
        )

    @typed_tasklet
    def get_event_team_avatars(
        self, event_key: EventKey
    ) -> Generator[Any, Any, Tuple[List[Media], Set[ndb.Key]]]:
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        parser = FMSAPITeamAvatarParser(year)
        api_event_short = DatafeedFMSAPI._get_event_short(year, event_short, event)
        avatars: List[Media] = []
        keys_to_delete: Set[ndb.Key] = set()

        more_pages = True
        page = 1

        while more_pages:
            avatar_result = yield self.api.event_team_avatars(
                year, api_event_short, page
            )
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
    @typed_tasklet
    def get_district_list(self, year: Year) -> Generator[Any, Any, List[District]]:
        district_list_response = yield self.api.district_list(year)
        result = self._parse(district_list_response, FMSAPIDistrictListParser(year))
        return result or []

    @typed_tasklet
    def get_district_rankings(
        self, district_key: DistrictKey
    ) -> Generator[Any, Any, DistrictAdvancement]:
        year = int(district_key[:4])
        district_short = district_key[4:]
        advancement: DistrictAdvancement = {}

        more_pages = True
        page = 1

        parser = FMSAPIDistrictRankingsParser()
        while more_pages:
            api_result = yield self.api.district_rankings(year, district_short, page)
            result = self._parse(api_result, parser)
            if not result:
                break

            advancement_page, more_pages = result
            advancement.update(advancement_page)
            page = page + 1

        return advancement

    @classmethod
    def _get_event_short(
        self, year: int, event_short: str, event: Optional[Event]
    ) -> str:
        if event:
            return event.first_api_code
        return Event.compute_first_api_code(year, event_short)

    def _parse(
        self, response: URLFetchResult, parser: ParserBase[TParsedResponse]
    ) -> Optional[TParsedResponse]:
        if response.status_code == 200:
            ApiStatusFMSApiDown.set_down(False)

            with Span(f"datafeed_fmsapi_parser:{type(parser).__name__}"):
                return parser.parse(response.json())

        elif response.status_code // 100 == 5:
            # 5XX error - something is wrong with the server
            ApiStatusFMSApiDown.set_down(True)

        logging.warning(
            f"Fetch for {response.url} failed; Error code {response.status_code}; {response.content}"
        )
        return None

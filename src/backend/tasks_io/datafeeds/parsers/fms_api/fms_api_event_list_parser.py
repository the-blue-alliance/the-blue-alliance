import datetime
import json
import logging
from typing import Any, cast, Dict, Generator, List, Optional, Set, Tuple

from google.appengine.ext import ndb
from pyre_extensions import none_throws
from pytz import all_timezones_set as PYTZ_ALL_TIMEZONES
from tzlocal.windows_tz import win_tz as WINDOWS_TO_IANA

from backend.common.consts.event_code_exceptions import EVENT_CODE_EXCEPTIONS
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.datafeeds.parsers.parser_base import ParserBase
from backend.common.frc_api.types import (
    SeasonEventListModelV31,
    SeasonEventListModelV33,
    SeasonEventModelV31,
    SeasonEventModelV33,
    WebcastDetailModelExtV33,
)
from backend.common.helpers.event_short_name_helper import EventShortNameHelper
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, Year
from backend.common.models.webcast import Webcast
from backend.common.tasklets import typed_tasklet


class FMSAPIEventListParser(
    ParserBase[
        SeasonEventListModelV33 | SeasonEventListModelV31,
        Tuple[List[Event], List[District]],
    ]
):
    DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S"

    EVENT_TYPES = {
        "regional": EventType.REGIONAL,
        "districtevent": EventType.DISTRICT,
        "districtchampionshipdivision": EventType.DISTRICT_CMP_DIVISION,
        "districtchampionship": EventType.DISTRICT_CMP,
        "districtchampionshipwithlevels": EventType.DISTRICT_CMP,
        "championshipdivision": EventType.CMP_DIVISION,
        "championshipsubdivision": EventType.CMP_DIVISION,
        "championship": EventType.CMP_FINALS,
        "offseason": EventType.OFFSEASON,
        "offseasonwithazuresync": EventType.OFFSEASON,
        "remote": EventType.REMOTE,
    }

    PLAYOFF_TYPES = {
        # Bracket Types
        "TwoAlliance": PlayoffType.BRACKET_2_TEAM,
        "FourAlliance": PlayoffType.BRACKET_4_TEAM,
        "EightAlliance": PlayoffType.BRACKET_8_TEAM,
        "SixteenAlliance": PlayoffType.BRACKET_16_TEAM,
        # Round Robin Types
        "SixAlliance": PlayoffType.ROUND_ROBIN_6_TEAM,
    }

    DOUBLE_ELIM_PLAYOFF_TYPES = {
        "FourAlliance": PlayoffType.DOUBLE_ELIM_4_TEAM,
        "EightAlliance": PlayoffType.DOUBLE_ELIM_8_TEAM,
    }

    NON_OFFICIAL_EVENT_TYPES = ["offseason"]

    EINSTEIN_SHORT_NAME_DEFAULT = "Einstein"
    EINSTEIN_NAME_DEFAULT = "Einstein Field"
    EINSTEIN_CODES = {"cmp", "cmpmi", "cmpmo", "cmptx"}

    def __init__(self, season: Year, short: str | None = None) -> None:
        self.season = season
        self.event_short = short

    def get_code_and_short_name(self, season, code):
        # Even though 2022/2023 Einstein is listed as "cmptx", we don't want it to say "(Houston)".
        if season >= 2022 and code == "cmptx":
            return (code, "{}")
        return EVENT_CODE_EXCEPTIONS[code]

    def get_playoff_type(self, year, alliance_count):
        playoff_type = None

        # 2023+ uses double elim.
        if year >= 2023:
            playoff_type = self.DOUBLE_ELIM_PLAYOFF_TYPES.get(alliance_count)

        if playoff_type is None:
            playoff_type = self.PLAYOFF_TYPES.get(alliance_count)

        return playoff_type

    def _bootstrap_sync_overrides(
        self,
        event_type: EventType,
        event_short: str,
        end_date: datetime.datetime,
        has_divisions: bool,
        has_division_teams_assigned: bool,
        existing_sync_overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        sync_overrides = dict(existing_sync_overrides)

        if (
            has_divisions
            and (
                end_date.date() < datetime.datetime.now().date()
                or has_division_teams_assigned
            )
            and event_type in {EventType.DISTRICT_CMP, EventType.CMP_FINALS}
        ):
            if "skip_eventteams" not in sync_overrides:
                sync_overrides["skip_eventteams"] = True
            if "set_start_day_to_last" not in sync_overrides:
                sync_overrides["set_start_day_to_last"] = True

        if "event_name_override" not in sync_overrides:
            if (
                event_type == EventType.CMP_FINALS
                and event_short in self.EINSTEIN_CODES
                and (
                    end_date.date() < datetime.datetime.now().date()
                    or has_division_teams_assigned
                )
            ):
                sync_overrides["event_name_override"] = {
                    "short_name": self.EINSTEIN_SHORT_NAME_DEFAULT,
                    "name": self.EINSTEIN_NAME_DEFAULT,
                }

        return sync_overrides

    @staticmethod
    @typed_tasklet
    def _parse_webcasts_async(
        api_webcasts: list[str] | list[WebcastDetailModelExtV33],
    ) -> Generator[Any, Any, List[Webcast]]:
        """Parse webcast URLs in parallel."""
        if api_webcasts and isinstance(api_webcasts[0], str):
            webcast_futures = tuple(
                WebcastParser.webcast_dict_from_url(cast(str, url))
                for url in api_webcasts
            )
            webcasts = yield webcast_futures
            return [w for w in webcasts if w is not None]

        webcasts = []
        if api_webcasts and isinstance(api_webcasts[0], dict):
            for api_webcast in api_webcasts:
                if w := WebcastParser.webcast_dict_from_api_response(
                    cast(WebcastDetailModelExtV33, api_webcast)
                ):
                    webcasts.append(w)

        raise ndb.Return(webcasts)

    def parse(
        self, response: SeasonEventListModelV33 | SeasonEventListModelV31
    ) -> Tuple[List[Event], List[District]]:
        events: List[Event] = []
        districts: Dict[DistrictKey, District] = {}

        api_events: list[SeasonEventModelV33] | list[SeasonEventModelV31] = (
            response["Events"] or []
        )

        district_cmp_division_districts: Set[str] = set()
        cmp_division_end_dates: List[datetime.datetime] = []
        for api_event in api_events:
            api_event_type = none_throws(api_event["type"]).lower()
            if api_event_type == "championshipdivision" and self.season < 2022:
                continue

            parsed_event_type = self.EVENT_TYPES.get(api_event_type, None)
            if parsed_event_type == EventType.DISTRICT_CMP_DIVISION and api_event.get(
                "districtCode"
            ):
                district_cmp_division_districts.add(
                    none_throws(api_event["districtCode"]).lower()
                )
            elif parsed_event_type == EventType.CMP_DIVISION:
                cmp_division_end_dates.append(
                    datetime.datetime.strptime(
                        none_throws(api_event["dateEnd"]), self.DATE_FORMAT_STR
                    )
                )

        event_keys_to_fetch = []
        for api_event in api_events:
            key_code = none_throws(api_event["code"]).lower()
            if key_code in EVENT_CODE_EXCEPTIONS:
                key_code, _ = self.get_code_and_short_name(self.season, key_code)
            elif self.event_short:
                key_code = self.event_short
            event_keys_to_fetch.append(f"{self.season}{key_code}")

        existing_events_by_key = {
            event.key_name: event
            for event in ndb.get_multi(
                [ndb.Key(Event, key) for key in event_keys_to_fetch]
            )
            if event is not None
        }

        for event in api_events:
            code = none_throws(event["code"]).lower()
            code_in_exceptions = code in EVENT_CODE_EXCEPTIONS

            api_event_type = none_throws(event["type"]).lower()
            event_type = (
                EventType.PRESEASON
                if code == "week0"
                else self.EVENT_TYPES.get(api_event_type, None)
            )
            if api_event_type == "championshipdivision" and self.season < 2022:
                # 2022 onward has one championship and the API uses ChampionshipSubdivision
                # for some reason. This didn't come up before because pre-2champs divisions
                # also reproted as ChampionshipSubDivision. Weird.
                logging.warning(
                    f"Skipping event {code} with type {api_event_type} as not a real division"
                )
                continue
            if event_type is None and not self.event_short:
                logging.warning(
                    "Event type '{}' not recognized!".format(api_event_type)
                )
                continue

            # Some event types should be marked as unofficial, so sync is disabled
            official = True
            if api_event_type in self.NON_OFFICIAL_EVENT_TYPES:
                official = False

            name = none_throws(event["name"])
            short_name = EventShortNameHelper.get_short_name(
                name,
                district_code=event["districtCode"],
                event_type=event_type,
                year=self.season,
            )

            if api_district_code := event["districtCode"]:
                district_key = District.render_key_name(
                    self.season, api_district_code.lower()
                )
            else:
                district_key = None

            address = event.get("address")
            venue = event["venue"]
            city = event["city"]
            state_prov = event["stateprov"]
            country = event["country"]
            start = datetime.datetime.strptime(event["dateStart"], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event["dateEnd"], self.DATE_FORMAT_STR)
            website = event.get("website")

            api_webcasts: list[str] | list[WebcastDetailModelExtV33] = []
            if resp_webcasts := event.get("webcasts"):
                api_webcasts = resp_webcasts

            webcasts: list[Webcast] = self._parse_webcasts_async(
                api_webcasts
            ).get_result()

            # Attempt to convert our API (Windows) timezone -> IANA timezone
            # We'll ensure it's capatiable with pytz as well, since that's what we use everywhere
            timezone = None
            if (
                (api_timezone := event.get("timezone"))
                and (iana_tz_name := WINDOWS_TO_IANA.get(api_timezone))
                and iana_tz_name in PYTZ_ALL_TIMEZONES
            ):
                timezone = iana_tz_name

            # Special cases for champs
            exception_short_name: Optional[str] = None
            if code_in_exceptions:
                code, exception_short_name = self.get_code_and_short_name(
                    self.season, code
                )

            elif self.event_short:
                code = self.event_short

            event_key = "{}{}".format(self.season, code)
            existing_event = existing_events_by_key.get(event_key)
            existing_sync_overrides: Dict[str, Any]
            if existing_event is not None and existing_event.sync_overrides is not None:
                existing_sync_overrides = dict(existing_event.sync_overrides)
            else:
                existing_sync_overrides = {}

            has_divisions = False
            has_division_teams_assigned = False
            first_api_code = None
            nexus_api_code = None
            if existing_event is not None and len(existing_event.divisions) > 0:
                has_divisions = True
                division_teams = EventTeam.query(
                    EventTeam.event.IN(existing_event.divisions)
                ).fetch(1, keys_only=True)
                has_division_teams_assigned = bool(division_teams)

            if event_type == EventType.DISTRICT_CMP and (
                district_code := event.get("districtCode")
            ):
                has_divisions = has_divisions or (
                    district_code.lower() in district_cmp_division_districts
                )
            elif event_type == EventType.CMP_FINALS:
                has_divisions = has_divisions or any(
                    abs(end - division_end_date) < datetime.timedelta(days=1)
                    for division_end_date in cmp_division_end_dates
                )
            elif event_type == EventType.OFFSEASON and existing_event:
                first_api_code = existing_event.first_code
                nexus_api_code = existing_event.nexus_code

            sync_overrides = self._bootstrap_sync_overrides(
                none_throws(event_type),
                code,
                end,
                has_divisions,
                has_division_teams_assigned,
                existing_sync_overrides,
            )

            if sync_overrides.get("event_sync_disable", False):
                continue

            if code_in_exceptions:
                # FIRST indicates CMP registration before divisions are assigned by adding all teams
                # to Einstein. We will hack around that by not storing divisions and renaming
                # Einstein to simply "Championship" when certain hack flags are set

                if code in self.EINSTEIN_CODES:
                    override = sync_overrides.get("event_name_override")
                    if override and exception_short_name:
                        name = exception_short_name.format(override["name"])
                        short_name = exception_short_name.format(override["short_name"])
                else:  # Divisions
                    if exception_short_name:
                        short_name = exception_short_name
                    name = "{} Division".format(short_name)

            # Allow an overriding the start date to be the beginning of the last day
            if sync_overrides.get("set_start_day_to_last", False):
                start = end.replace(hour=0, minute=0, second=0, microsecond=0)

            playoff_type = self.get_playoff_type(
                self.season, event.get("allianceCount")
            )

            events.append(
                Event(
                    id=event_key,
                    name=name,
                    short_name=short_name,
                    event_short=code,
                    event_type_enum=event_type,
                    timezone_id=timezone,
                    official=official,
                    first_code=first_api_code,
                    nexus_code=nexus_api_code,
                    playoff_type=playoff_type,
                    start_date=start,
                    end_date=end,
                    venue=venue,
                    city=city,
                    state_prov=state_prov,
                    country=country,
                    venue_address=address,
                    year=self.season,
                    district_key=(
                        ndb.Key(District, district_key) if district_key else None
                    ),
                    website=website,
                    sync_overrides=sync_overrides,
                    webcast_json=json.dumps(webcasts) if webcasts else None,
                )
            )

            # Build District Model
            if (
                (district_code := event["districtCode"])
                and district_key
                and district_key not in districts
            ):
                districts[district_key] = District(
                    id=district_key,
                    year=self.season,
                    abbreviation=district_code.lower(),
                )

        # Prep for division <-> parent associations
        district_champs_by_district = {}
        champ_events = []
        for event in events:
            if event.event_type_enum == EventType.DISTRICT_CMP:
                district_champs_by_district[event.district_key] = event
            elif event.event_type_enum == EventType.CMP_FINALS:
                champ_events.append(event)

        # Build district cmp division <-> parent associations based on district
        # Build cmp division <-> parent associations based on date
        for event in events:
            parent_event = None
            if event.event_type_enum == EventType.DISTRICT_CMP_DIVISION:
                parent_event = district_champs_by_district.get(event.district_key)
            elif event.event_type_enum == EventType.CMP_DIVISION:
                for parent_event in champ_events:
                    if abs(parent_event.end_date - event.end_date) < datetime.timedelta(
                        days=1
                    ):
                        break
                else:
                    parent_event = None
            else:
                continue

            if parent_event is None:
                continue

            parent_event.divisions = sorted(parent_event.divisions + [event.key])
            event.parent_event = parent_event.key

        return events, list(districts.values())

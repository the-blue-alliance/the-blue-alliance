import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.consts.event_code_exceptions import EVENT_CODE_EXCEPTIONS
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.event_short_name_helper import EventShortNameHelper
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.keys import DistrictKey, Year
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.tasks_io.datafeeds.parsers.json.parser_json import ParserJSON


class FMSAPIEventListParser(ParserJSON[Tuple[List[Event], List[District]]]):
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

    def __init__(self, season: Year, short: Optional[str] = None) -> None:
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

    def parse(self, response: Dict[str, Any]) -> Tuple[List[Event], List[District]]:
        events: List[Event] = []
        districts: Dict[DistrictKey, District] = {}

        cmp_hack_sitevar = ChampsRegistrationHacks.get()
        divisions_to_skip = cmp_hack_sitevar["divisions_to_skip"]
        event_name_override = cmp_hack_sitevar["event_name_override"]
        events_to_change_dates = cmp_hack_sitevar["set_start_to_last_day"]

        for event in response["Events"]:
            code = event["code"].lower()

            api_event_type = event["type"].lower()
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

            name = event["name"]
            short_name = EventShortNameHelper.get_short_name(
                name,
                district_code=event["districtCode"],
                event_type=event_type,
                year=self.season,
            )
            district_key = (
                District.render_key_name(self.season, event["districtCode"].lower())
                if event["districtCode"]
                else None
            )
            address = event.get("address")
            venue = event["venue"]
            city = event["city"]
            state_prov = event["stateprov"]
            country = event["country"]
            start = datetime.datetime.strptime(event["dateStart"], self.DATE_FORMAT_STR)
            end = datetime.datetime.strptime(event["dateEnd"], self.DATE_FORMAT_STR)
            website = event.get("website")
            webcasts = [
                WebcastParser.webcast_dict_from_url(url)
                for url in event.get("webcasts", [])
            ]

            # TODO read timezone from API

            # Special cases for champs
            if code in EVENT_CODE_EXCEPTIONS:
                code, short_name = self.get_code_and_short_name(self.season, code)

                # FIRST indicates CMP registration before divisions are assigned by adding all teams
                # to Einstein. We will hack around that by not storing divisions and renaming
                # Einstein to simply "Championship" when certain sitevar flags are set

                if code in self.EINSTEIN_CODES:
                    override = [
                        item
                        for item in event_name_override
                        if item["event"] == "{}{}".format(self.season, code)
                    ]
                    if override:
                        name = short_name.format(override[0]["name"])
                        short_name = short_name.format(override[0]["short_name"])
                else:  # Divisions
                    name = "{} Division".format(short_name)
            elif self.event_short:
                code = self.event_short

            event_key = "{}{}".format(self.season, code)
            if event_key in divisions_to_skip:
                continue

            # Allow an overriding the start date to be the beginning of the last day
            if event_key in events_to_change_dates:
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
                    official=official,
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
                    webcast_json=json.dumps(webcasts) if webcasts else None,
                )
            )

            # Build District Model
            if district_key and district_key not in districts:
                districts[district_key] = District(
                    id=district_key,
                    year=self.season,
                    abbreviation=event["districtCode"].lower(),
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

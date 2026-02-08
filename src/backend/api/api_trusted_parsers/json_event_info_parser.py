import re
from datetime import datetime
from typing import TypedDict

import pytz
from pyre_extensions import safe_json

from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.models.keys import TeamKey
from backend.common.models.webcast import Webcast


# We let users pass either a regular webcast model (type+channel),
# or a dict with 'url' as a key, which we can parse into a model
class _WebcastUrlDict(TypedDict, total=False):
    url: str
    type: WebcastType
    channel: str
    date: str


class EventInfoInput(TypedDict, total=False):
    first_event_code: str | None
    playoff_type: int
    webcasts: list[_WebcastUrlDict]
    remap_teams: dict[str, str]
    disable_sync: dict[str, bool]


class EventInfoParsed(TypedDict, total=False):
    first_event_code: str | None
    playoff_type: PlayoffType | None
    webcasts: list[Webcast]
    remap_teams: dict[TeamKey, TeamKey]
    timezone: str
    sync_disabled_flags: int


class JSONEventInfoParser:
    @staticmethod
    def _parse_webcast(webcast: _WebcastUrlDict) -> Webcast:
        if url := webcast.get("url"):
            parsed_webcast = WebcastParser.webcast_dict_from_url(url).get_result()
            if not parsed_webcast:
                raise ParserInputException(f"Unknown webcast url {url}!")
        elif (webcast_type := webcast.get("type")) and (
            channel := webcast.get("channel")
        ):
            parsed_webcast = Webcast(type=webcast_type, channel=channel)
        else:
            raise ParserInputException(f"Invalid webcast: {webcast!r}")

        if date := webcast.get("date"):
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError as e:
                raise ParserInputException(f"Invalid webcast date: {date!r}: {e}")
            parsed_webcast["date"] = date

        return parsed_webcast

    @staticmethod
    def parse[T: (str, bytes)](info_json: T) -> EventInfoParsed:
        # pyre validation doesn't support non-total TypedDict
        info_dict = safe_json.loads(info_json, EventInfoInput, validate=False)

        parsed_info: EventInfoParsed = {}
        if webcasts := info_dict.get("webcasts"):
            parsed_info["webcasts"] = [
                JSONEventInfoParser._parse_webcast(w) for w in webcasts
            ]

        if remap_teams := info_dict.get("remap_teams"):
            for temp_team, remapped_team in remap_teams.items():
                temp_match = re.fullmatch(r"frc(\d+)", str(temp_team))
                if not temp_match:
                    raise ParserInputException(
                        f"Bad team: '{temp_team}'. Must follow format 'frcXXX'."
                    )
                remapped_match = re.fullmatch(r"frc(\d+)[B-Z]?", str(remapped_team))
                if not remapped_match:
                    raise ParserInputException(
                        f"Bad team: '{remapped_team}'. Must follow format 'frcXXX' or 'frcXXX[B-Z]'."
                    )
            parsed_info["remap_teams"] = remap_teams

        if "playoff_type" in info_dict:
            playoff_type = info_dict["playoff_type"]
            if playoff_type is None:
                parsed_info["playoff_type"] = None
            elif playoff_type in PlayoffType._value2member_map_:
                parsed_info["playoff_type"] = PlayoffType(playoff_type)
            else:
                raise ParserInputException(f"Bad playoff type: {playoff_type}")

        if "first_event_code" in info_dict:
            parsed_info["first_event_code"] = info_dict["first_event_code"]

        if timezone := info_dict.get("timezone"):
            if timezone not in pytz.all_timezones_set:
                raise ParserInputException(f"Unknown timezone {timezone}")
            parsed_info["timezone"] = timezone

        if sync_disabled_dict := info_dict.get("disable_sync"):
            if not isinstance(sync_disabled_dict, dict):
                raise ParserInputException("disable_sync must be a dict")
            sync_types = EventSyncType.__members__.items()
            dict_keys = set(sync_disabled_dict.keys())
            valid_keys = {name.lower() for name, _ in sync_types}
            invalid_keys = dict_keys - valid_keys
            if invalid_keys:
                raise ParserInputException(
                    f"Invalid keys in disable_sync dict: {invalid_keys}. Valid keys: {valid_keys}"
                )

            sync_flags = 0
            for name, val in sync_types:
                if sync_disabled_dict.get(name.lower()):
                    sync_flags |= val
            parsed_info["sync_disabled_flags"] = sync_flags

        return parsed_info

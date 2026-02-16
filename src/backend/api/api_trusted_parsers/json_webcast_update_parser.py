from datetime import datetime
from typing import List, TypedDict

from pyre_extensions import safe_json

from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.models.webcast import Webcast


# We let users pass either a regular webcast model (type+channel),
# or a dict with 'url' as a key, which we can parse into a model
class _WebcastUrlDict(TypedDict, total=False):
    url: str
    type: WebcastType
    channel: str
    file: str
    date: str


class WebcastUpdateInput(TypedDict, total=False):
    webcasts: List[_WebcastUrlDict]


class WebcastUpdateParsed(TypedDict, total=False):
    webcasts: List[Webcast]


class JSONWebcastUpdateParser:
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

        if file := webcast.get("file"):
            parsed_webcast["file"] = file

        if date := webcast.get("date"):
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError as e:
                raise ParserInputException(f"Invalid webcast date: {date!r}: {e}")
            parsed_webcast["date"] = date

        return parsed_webcast

    @staticmethod
    def parse[T: (str, bytes)](webcast_json: T) -> WebcastUpdateParsed:
        # pyre validation doesn't support non-total TypedDict
        webcast_dict = safe_json.loads(webcast_json, WebcastUpdateInput, validate=False)

        parsed_data: WebcastUpdateParsed = {}
        if webcasts := webcast_dict.get("webcasts"):
            if not isinstance(webcasts, list):
                raise ParserInputException("webcasts must be a list")
            parsed_data["webcasts"] = [
                JSONWebcastUpdateParser._parse_webcast(w) for w in webcasts
            ]

        return parsed_data

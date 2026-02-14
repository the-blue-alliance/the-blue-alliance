from typing import List, TypedDict

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.webcast import Webcast, WebcastType


class _WebcastDict(TypedDict, total=False):
    type: WebcastType
    channel: str
    file: str
    url: str
    date: str


class WebcastUpdateInput(TypedDict, total=False):
    webcasts: List[_WebcastDict]


class WebcastUpdateParsed(TypedDict, total=False):
    webcasts: List[Webcast]


class JSONWebcastUpdateParser:
    @staticmethod
    def parse[T: (str, bytes)](webcast_json: T) -> WebcastUpdateParsed:
        # pyre validation doesn't support non-total TypedDict
        webcast_dict = safe_json.loads(webcast_json, WebcastUpdateInput, validate=False)

        parsed_data: WebcastUpdateParsed = {}
        if webcasts := webcast_dict.get("webcasts"):
            if not isinstance(webcasts, list):
                raise ParserInputException("webcasts must be a list")
            parsed_data["webcasts"] = webcasts

        return parsed_data

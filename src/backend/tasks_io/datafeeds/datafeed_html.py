import abc
import logging
from typing import (
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
)

import requests

from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


TModel = TypeVar("TModel")
TParser = TypeVar("TParser", bound=ParserBase)


class DatafeedHTML(abc.ABC, Generic[TParser, TModel]):
    """
    Provides structure for fetching and parsing pages from websites.
    Other Datafeeds inherit from here.
    """

    def parse(
        self, url: str, parser: TParser, usfirst_session_key: Optional[str] = None
    ) -> Tuple[List[TModel], bool]:
        headers = {
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
        }

        if "my.usfirst.org/myarea" in url:
            # FIRST is now checking the "Referer" header for the string "usfirst.org".
            # See https://github.com/patfair/frclinks/commit/051bf91d23ca0242dad5b1e471f78468173f597f
            headers["Referer"] = "usfirst.org"

        if usfirst_session_key is not None:
            headers["Cookie"] = usfirst_session_key

        try:
            result = requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            logging.error(f"URLFetch failed for: {url}")
            logging.info(e)
            return [], False

        if result.status_code == 200:
            return parser.parse(result.content)
        else:
            logging.warning(f"Unable to retreive url: {url}")
            return [], False

    # def _shorten(self, string: str):
    #     MAX_DB_LENGTH = 500
    #     if string:
    #         return string[:MAX_DB_LENGTH]
    #     else:
    #         return string

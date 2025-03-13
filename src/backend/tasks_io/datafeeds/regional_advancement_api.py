from typing import Any, Generator

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.profiler import Span
from backend.common.sitevars.regional_advancement_api_secrets import (
    RegionalAdvancementApiSecret,
)
from backend.common.tasklets import typed_tasklet
from backend.common.urlfetch import URLFetchResult


class RegionalAdvancementApi:

    def __init__(self, year: Year) -> None:
        if not SeasonHelper.is_valid_regional_pool_year(year):
            raise Exception(f"Invalid year for regional pool: {year}")

        url_fmt = RegionalAdvancementApiSecret.url_format()
        if not url_fmt:
            raise Exception("Missing regional pool API url!")

        self.year = year
        self.url = url_fmt.format(year=year)
        self.ndb_context = ndb.get_context()

    def cmp_advancement(self) -> TypedFuture[URLFetchResult]:
        return self._get()

    @typed_tasklet
    def _get(self) -> Generator[Any, Any, URLFetchResult]:
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
        }

        with Span(f"regional_advancemnet_fetch:{self.year}"):
            resp = yield self.ndb_context.urlfetch(
                self.url, headers=headers, deadline=30
            )
            return URLFetchResult(self.url, resp)

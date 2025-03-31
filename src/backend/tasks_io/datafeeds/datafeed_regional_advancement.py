from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.sitevars.regional_advancement_api_secrets import (
    RegionalAdvancementApiSecret,
)
from backend.tasks_io.datafeeds.datafeed_base import DatafeedBase, TReturn
from backend.tasks_io.datafeeds.parsers.ra.regional_advancement_parser import (
    RegionalAdvancementParser,
    TParsedRegionalAdvancement,
)


class _DatafeedRegionalAdvancement(DatafeedBase[TReturn]):

    def __init__(self, year: Year) -> None:
        if not SeasonHelper.is_valid_regional_pool_year(year):
            raise Exception(f"Invalid year for regional pool: {year}")
        self.year = year

    def headers(self):
        return {
            "Accept": "application/json",
            "Cache-Control": "no-cache, max-age=10",
            "Pragma": "no-cache",
        }


class RegionalChampsAdvancement(
    _DatafeedRegionalAdvancement[TParsedRegionalAdvancement]
):

    def __init__(self, year: Year) -> None:
        super().__init__(year)
        url_fmt = RegionalAdvancementApiSecret.url_format()
        if not url_fmt:
            raise Exception("Missing regional pool API url!")

        self.url_fmt = url_fmt

    def url(self):
        return self.url_fmt.format(year=self.year)

    def parser(self) -> RegionalAdvancementParser:
        return RegionalAdvancementParser()

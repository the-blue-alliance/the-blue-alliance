from typing import Iterable

from backend.common.models.keys import Year
from backend.common.sitevars.apistatus import ApiStatus


class SeasonHelper(object):

    MIN_YEAR: Year = 1992

    @staticmethod
    def get_max_year() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["max_season"]

    @staticmethod
    def get_current_season() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["current_season"]

    @classmethod
    def get_valid_years(cls) -> Iterable[Year]:
        max_year = cls.get_max_year()
        return range(cls.MIN_YEAR, max_year + 1)
